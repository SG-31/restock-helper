import sqlite3


DATABASE = "database/restock.db"


def get_connection():
    """SQLiteへの接続を作成する。"""
    connection = sqlite3.connect(DATABASE)

    # カラム名でデータを取得できるようにする
    connection.row_factory = sqlite3.Row

    # この接続でも外部キー制約を有効にする
    connection.execute("PRAGMA foreign_keys = ON")

    return connection