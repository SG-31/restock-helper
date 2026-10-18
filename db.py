import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row


def get_connection():
    """PostgreSQLへの接続を作成する。"""

    if "DATABASE_URL" not in os.environ or not os.environ["DATABASE_URL"].strip():
        raise RuntimeError(
            "環境変数 DATABASE_URL が設定されていません。"
            ".envファイルにDATABASE_URLを設定してください。"
        )

    return psycopg.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=10,
        row_factory=dict_row,
    )


@contextmanager
def get_connection_context():
    """DB接続をwith文で安全に管理する。"""
    connection = get_connection()

    try:
        yield connection
        connection.commit()
    except psycopg.Error:
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
        WHERE id = %s
        """,
        (item_id,),
    ).fetchone()


def get_consumptions(connection, item_id):
    """指定した管理品目の直近4件の消費量を取得する。"""
    return connection.execute(
        """
        SELECT consumption
        FROM consumptions
        WHERE item_id = %s
        ORDER BY recorded_at DESC, id DESC
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


def item_name_exists(connection, name, item_id=None):
    """指定した名前の管理品目が存在するか確認する。"""
    if item_id is None:
        row = connection.execute(
            """
            SELECT 1
            FROM items
            WHERE TRIM(name) = %s
            LIMIT 1
            """,
            (name,),
        ).fetchone()
    else:
        row = connection.execute(
            """
            SELECT 1
            FROM items
            WHERE TRIM(name) = %s
              AND id != %s
            LIMIT 1
            """,
            (name, item_id),
        ).fetchone()

    return row is not None
