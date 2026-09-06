import sqlite3

from flask import Flask

from routes.items import items_bp
import db


app = Flask(__name__)


# =========================
# DB初期化
# =========================

def init_db():
    connection = None

    try:
        # DBに接続
        connection = db.get_connection()

        # itemsテーブル
        connection.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            )
        """)

        # consumptionsテーブル
        connection.execute("""
            CREATE TABLE IF NOT EXISTS consumptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                consumption INTEGER NOT NULL CHECK (consumption >= 0),
                recorded_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        """)

        # shopping_memosテーブル
        connection.execute("""
            CREATE TABLE IF NOT EXISTS shopping_memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            )
        """)

        # ここまで成功したらDBに確定
        connection.commit()

        print("DB初期化が完了しました。")
        return True

    except sqlite3.Error as error:
        # DB関連のエラー内容を表示
        print(f"DB初期化エラー: {error}")
        return False

    finally:
        # 接続できていた場合は必ず閉じる
        if connection is not None:
            connection.close()


# =========================
# Blueprint登録
# =========================

app.register_blueprint(items_bp)


# =========================
# アプリ起動
# =========================

if __name__ == "__main__":
    # DB初期化に失敗したらFlaskを起動しない
    if not init_db():
        print("DBを利用できないため、Flaskサーバーを起動しません。")
    else:
        app.run(debug=True)