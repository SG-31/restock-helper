import sqlite3
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    # SQLiteに接続できるか確認する
    connection = sqlite3.connect("restock.db")
    connection.close()

    return "SQLite connection OK!"


if __name__ == "__main__":
    app.run(debug=True)