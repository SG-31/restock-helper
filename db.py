import os
import sqlite3
from contextlib import contextmanager


DATABASE = "database/restock.db"


def get_connection():
    """SQLiteへの接続を作成する。"""

    # DBファイルを保存するフォルダがなければ作成する
    os.makedirs("database", exist_ok=True)

    connection = sqlite3.connect(DATABASE)

    # カラム名でデータを取得できるようにする
    connection.row_factory = sqlite3.Row

    # この接続でも外部キー制約を有効にする
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


@contextmanager
def get_connection_context():
    """DB接続をwith文で安全に管理する。"""
    connection = get_connection()

    try:
        yield connection
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_items(connection):
    """管理品目をID順に取得する。"""
    return connection.execute(
        """
        SELECT id, name, unit, current_stock
        FROM items
        ORDER BY id
        """
    ).fetchall()


def get_item(connection, item_id):
    """指定したIDの管理品目を1件取得する。存在しなければNoneを返す。"""
    return connection.execute(
        """
        SELECT id, name, unit, current_stock
        FROM items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()


def get_consumptions(connection, item_id):
    """指定した管理品目の直近4件の消費量を取得する。"""
    return connection.execute(
        """
        SELECT consumption
        FROM consumptions
        WHERE item_id = ?
        ORDER BY recorded_at DESC
        LIMIT 4
        """,
        (item_id,),
    ).fetchall()


def build_restock_list(connection, items):
    """管理品目ごとの補充情報をまとめて取得する。"""
    from calculations import calc_restock_info

    restock_list = []

    for item in items:
        consumptions = get_consumptions(connection, item["id"])

        consumption_values = [
            consumption["consumption"] for consumption in consumptions
        ]

        restock_info = calc_restock_info(item, consumption_values)

        if restock_info is not None:
            restock_list.append(restock_info)

    return restock_list


def get_shopping_list(connection):
    """現在の補充必要数から買い物リストを取得する。"""
    items = get_items(connection)
    return build_restock_list(connection, items)
