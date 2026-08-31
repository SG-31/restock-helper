import sqlite3
from flask import Flask

app = Flask(__name__)


def init_db():
    # SQLiteデータベースに接続する
    connection = sqlite3.connect("restock.db")

    # SQLiteで外部キーの機能を有効にする
    connection.execute("PRAGMA foreign_keys = ON")

    # 管理品目のテーブルを作成する
    connection.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # データベースへの変更を確定する
    connection.commit()

    # データベースとの接続を閉じる
    connection.close()


@app.route("/")
def hello():
    return "Restock Helper DB OK!"


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
