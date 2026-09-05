import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)

DATABASE = "database/restock.db"

# =========================
# DB初期化
# =========================

def init_db():

    connection = None

    try:
        # DBに接続
        connection = sqlite3.connect(DATABASE)

        # SQLiteの外部キー制約を有効にする
        connection.execute("PRAGMA foreign_keys = ON")

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
# 管理品目一覧
# =========================

@app.route("/items")
def items():
       
    connection = None

    try:
        # DBに接続
        connection = sqlite3.connect(DATABASE)

        # 管理品目をID順に取得
        cursor = connection.execute(
            """
            SELECT id, name, unit, current_stock
            FROM items
            ORDER BY id
            """
        )

        # 取得した全データをリストにする
        items = cursor.fetchall()

        # HTMLにitemsを渡す
        return render_template("items.html", items=items)

    except sqlite3.Error as error:
        print(f"管理品目一覧の取得エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error=f"管理品目一覧を取得できませんでした。DBエラー: {error}"
        )

    finally:
        # DB接続ができていた場合は必ず閉じる
        if connection is not None:
            connection.close()

# =========================
# 管理品目登録
# =========================

@app.route("/items/new", methods=["GET", "POST"])
def new_item():
    # GETの場合：登録フォームを表示する
    if request.method == "GET":
        return render_template("item_form.html", action_url="/items/new")
        

    # POSTの場合：フォームから送信されたデータを保存する
    name = request.form.get("name", "").strip()
    unit = request.form.get("unit", "").strip()
    stock_text = request.form.get("current_stock", "").strip()

    # 初期在庫数を整数に変換する
    try:
        current_stock = int(stock_text)
    except ValueError:
        return render_template(
            "item_form.html",
            error="初期在庫数は整数で入力してください。",
            action_url="/items/new"
        )

    # 初期在庫数がマイナスの場合は保存しない
    if current_stock < 0:
        return render_template(
            "item_form.html",
            error="初期在庫数は0以上で入力してください。",
            action_url="/items/new"
        )

    connection = None

    try:
        # DBに接続
        connection = sqlite3.connect(DATABASE)

        # itemsテーブルに新しい品目を登録
        connection.execute(
            """
            INSERT INTO items (name, unit, current_stock)
            VALUES (?, ?, ?)
            """,
            (name, unit, current_stock)
        )

        connection.commit()

        return render_template(
            "item_form.html",
            message="管理品目を登録しました。",
            action_url="/items/new"
        )

    except sqlite3.Error as error:
        print(f"管理品目の登録エラー: {error}")

        return render_template(
            "item_form.html",
            error=f"管理品目を登録できませんでした。DBエラー: {error}",
            action_url="/items/new"
        )

    finally:
        # DB接続ができていた場合は必ず閉じる
        if connection is not None:
            connection.close()

# =========================
# 管理品目編集
# =========================

@app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):

    connection = None

    try:
        # DBに接続
        connection = sqlite3.connect(DATABASE)

        # カラム名でデータを取得できるようにする
        connection.row_factory = sqlite3.Row

        # 指定されたIDの管理品目を取得
        cursor = connection.execute(
            """
            SELECT id, name, unit, current_stock
            FROM items
            WHERE id = ?
            """,
            (item_id,)
        )

        item = cursor.fetchone()

        # 指定されたIDの品目が存在しない場合
        if item is None:
            return "品目が見つかりません。", 404

        # GETの場合：現在の値をフォームに表示する
        if request.method == "GET":
            return render_template(
                "item_form.html",
                item=item,
                action_url=f"/items/{item_id}/edit"
            )

        # POSTの場合：フォームから送信されたデータを取得
        name = request.form.get("name", "").strip()
        unit = request.form.get("unit", "").strip()
        stock_text = request.form.get("current_stock", "").strip()

        # 現在庫数を整数に変換する
        try:
            current_stock = int(stock_text)
        except ValueError:
            return render_template(
                "item_form.html",
                item=item,
                action_url=f"/items/{item_id}/edit",
                error="現在庫数は整数で入力してください。"
            )

        # 現在庫数がマイナスの場合は更新しない
        if current_stock < 0:
            return render_template(
                "item_form.html",
                item=item,
                action_url=f"/items/{item_id}/edit",
                error="現在庫数は0以上で入力してください。"
            )

        # 管理品目を更新
        connection.execute(
            """
            UPDATE items
            SET name = ?,
                unit = ?,
                current_stock = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name, unit, current_stock, item_id)
        )

        # 更新を確定
        connection.commit()

        # 更新後の値をフォームに表示する
        updated_item = connection.execute(
            """
            SELECT id, name, unit, current_stock
            FROM items
            WHERE id = ?
            """,
            (item_id,)
        ).fetchone()

        return render_template(
            "item_form.html",
            item=updated_item,
            action_url=f"/items/{item_id}/edit",
            message="管理品目を変更しました。"
        )

    except sqlite3.Error as error:
        print(f"管理品目の変更エラー: {error}")
        return render_template(
            "item_form.html",
            item=None,
            action_url=f"/items/{item_id}/edit",
            error=f"管理品目を変更できませんでした。DBエラー: {error}"
        )

    finally:
        # DB接続ができていた場合は必ず閉じる
        if connection is not None:
            connection.close()


# =========================
# アプリ起動
# =========================

if __name__ == "__main__":
    # DB初期化に失敗したらFlaskを起動しない
    if not init_db():
        print("DBを利用できないため、Flaskサーバーを起動しません。")
    else:
        app.run(debug=True)
