import hmac
import os
from datetime import timedelta

import psycopg
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFError, CSRFProtect

from db import get_connection_context

from routes.items import items_bp
from routes.stock import stock_bp
from routes.shopping import shopping_bp


# ローカル開発では.envから環境変数を読み込む
load_dotenv()

app = Flask(
    __name__,
    static_folder="public/static",
    static_url_path="/static",
)

# セッション・flashメッセージ用の秘密鍵
secret_key = os.getenv("SECRET_KEY", "").strip()

if not secret_key:
    raise SystemExit("SECRET_KEYが設定されていないため、アプリを起動しません。")

app.secret_key = secret_key


# 共通ログインパスワードを環境変数から読み込む
app_password = os.getenv("APP_PASSWORD", "").strip()

# 未設定または空白のみの場合は起動を停止する
# 比較に使用するパスワード自体は、前後の空白を削除しない
if not app_password:
    raise SystemExit("APP_PASSWORDが設定されていないため、アプリを起動しません。")


# セッションCookieの設定
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# VercelではHTTPS専用、ローカル開発ではHTTPでも使用できるようにする
app.config["SESSION_COOKIE_SECURE"] = os.getenv("VERCEL") == "1"


# CSRF攻撃を防止する
# before_requestの順番を制御するため、初期化は後で行う
csrf = CSRFProtect()

# ヘルパーが在庫を数えている間にトークンが期限切れにならないよう、
# CSRFトークンの有効期限をなくす
app.config["WTF_CSRF_TIME_LIMIT"] = None


# トップ案内画面
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# ログイン
# =========================


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "").strip()

        # UTF-8に変換することで、日本語を含むパスワードにも対応する
        # compare_digestで文字列を直接比較するより安全に比較する
        if hmac.compare_digest(
            password.encode("utf-8"),
            app_password.encode("utf-8"),
        ):
            # 古いセッション情報を破棄してからログイン状態を設定する
            session.clear()
            session["logged_in"] = True
            session.permanent = True

            # ログイン後の移動先は常にトップ画面
            return redirect(url_for("index"))

        # パスワードが違う場合
        # 入力値をテンプレートに渡さないため、入力欄は空になる
        flash("パスワードが違います。", "error")

    return render_template("login.html")


# =========================
# ログアウト
# =========================


@app.route("/logout", methods=["POST"])
def logout():
    # ログイン状態を含むセッションを破棄する
    session.clear()

    # ログアウト後、ログイン画面で通知する
    flash("ログアウトしました。")

    return redirect(url_for("login"))


# =========================
# ログイン必須のアクセス制御
# =========================


@app.before_request
def require_login():
    # ログイン画面とFlaskの静的ファイルは対象外
    if request.endpoint in {"login", "static"}:
        return None

    # ログイン済みでなければログイン画面へ移動
    if session.get("logged_in") is not True:
        return redirect(url_for("login"))

    return None


# アクセス制御を登録した後にCSRF保護を初期化する
# これにより、ログイン確認がCSRF確認より先に実行される
csrf.init_app(app)


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    print(f"CSRFエラー: {error.description}")
    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>操作エラー</title>
    </head>
    <body>
        <h1>操作できませんでした</h1>
        <p>画面の有効期限が切れたか、送信内容を確認できませんでした。画面を開き直してから、もう一度操作してください。</p>
        <p><a href="/">トップに戻る</a></p>
    </body>
    </html>
    """
    return html, 400


# =========================
# DB初期化
# =========================


def init_db():
    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with get_connection_context() as connection:
            # itemsテーブル
            connection.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    unit TEXT NOT NULL,
                    current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # consumptionsテーブル
            connection.execute("""
                CREATE TABLE IF NOT EXISTS consumptions (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    consumption INTEGER NOT NULL CHECK (consumption >= 0),
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            """)

            # shopping_memosテーブル
            connection.execute("""
                CREATE TABLE IF NOT EXISTS shopping_memos (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

        print("DB初期化が完了しました。")
        return True

    except (psycopg.Error, RuntimeError) as error:
        # DB接続・初期化に失敗した原因を表示
        print(f"DB初期化エラー: {error}")
        return False


# =========================
# Blueprint登録
# =========================
app.register_blueprint(items_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(shopping_bp)


# アプリ読み込み時にDBを初期化する
db_initialized = init_db()

if not db_initialized:
    raise SystemExit("DBを利用できないため、アプリを起動しません。")


# 環境変数でデバッグモードを切り替える
debug_mode = os.getenv("FLASK_DEBUG", "").lower() == "true"

# =========================
# アプリ起動
# =========================
if __name__ == "__main__":
    app.run(debug=debug_mode)
