"""Restock Helperのデモ用見本データを登録するスクリプト。

実行方法:
    python -m scripts.seed_demo

注意:
    実行を確定すると、接続先DBの既存データをすべて削除します。
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit

import psycopg
from dotenv import load_dotenv

from db import get_connection_context


# =========================
# 見本データ
# =========================

# 品目名、単位、現在庫、消費量（28日前・21日前・14日前・7日前）
DEMO_ITEMS = [
    {
        "name": "トイレットペーパー",
        "unit": "ロール",
        "current_stock": 3,
        "consumptions": (4, 5, 4, 3),
    },
    {
        "name": "ティッシュペーパー",
        "unit": "箱",
        "current_stock": 4,
        "consumptions": (1, 1, 2, 1),
    },
    {
        "name": "牛乳",
        "unit": "本",
        "current_stock": 1,
        "consumptions": (3, 2, 3, 2),
    },
    {
        "name": "卵",
        "unit": "パック",
        "current_stock": 0,
        "consumptions": (1, 1, 1, 1),
    },
    {
        "name": "食器用洗剤",
        "unit": "本",
        "current_stock": 2,
        "consumptions": (0, 1, 0, 0),
    },
    {
        "name": "米（5kg）",
        "unit": "袋",
        "current_stock": 1,
        "consumptions": (0, 1, 0, 0),
    },
]

DEMO_MEMOS = [
    "単3電池 4本",
    "のど飴",
]

# 古い記録から順に登録する
CONSUMPTION_DAYS = (28, 21, 14, 7)

# テーブルが存在するか確認する対象
REQUIRED_TABLES = (
    "items",
    "consumptions",
    "shopping_memos",
)


def get_database_target(database_url):
    """接続URLからホスト名とDB名を取得する。

    パスワードを含む接続URLそのものは表示しない。
    """
    parsed_url = urlsplit(database_url)

    host = parsed_url.hostname
    database_name = unquote(parsed_url.path.lstrip("/"))

    if not host or not database_name:
        raise ValueError

    return host, database_name


def confirm_data_replacement(host, database_name):
    """接続先を表示し、データの全削除について確認する。"""
    print(f"接続先ホスト: {host}")
    print(f"データベース名: {database_name}")
    print(
        "このDBのデータをすべて消して、"
        "見本データを入れます。"
        "よろしければ yes と入力してください：",
        end="",
        flush=True,
    )

    answer = input()

    if answer != "yes":
        print("キャンセルしました。データは変更していません。")
        return False

    return True


def tables_exist(connection):
    """必要な3テーブルが存在するか確認する。"""
    result = connection.execute(
        """
        SELECT
            to_regclass(%s) AS items_table,
            to_regclass(%s) AS consumptions_table,
            to_regclass(%s) AS shopping_memos_table
        """,
        REQUIRED_TABLES,
    ).fetchone()

    return all(result[f"{table}_table"] is not None for table in REQUIRED_TABLES)


def insert_demo_data(connection):
    """同一トランザクション内で既存データを置き換える。"""

    # 3テーブルのデータを削除し、IDENTITYの採番をリセットする
    connection.execute(
        """
        TRUNCATE consumptions, shopping_memos, items
        RESTART IDENTITY
        """
    )

    # すべての消費記録で基準時刻を統一する
    now = datetime.now(timezone.utc)

    for item in DEMO_ITEMS:
        # IDはDBに採番させる
        result = connection.execute(
            """
            INSERT INTO items (name, unit, current_stock)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                item["name"],
                item["unit"],
                item["current_stock"],
            ),
        ).fetchone()

        item_id = result["id"]

        # 古い記録から新しい記録の順に登録する
        for days_ago, consumption in zip(
            CONSUMPTION_DAYS,
            item["consumptions"],
        ):
            recorded_at = now - timedelta(days=days_ago)

            connection.execute(
                """
                INSERT INTO consumptions (
                    item_id,
                    consumption,
                    recorded_at
                )
                VALUES (%s, %s, %s)
                """,
                (
                    item_id,
                    consumption,
                    recorded_at,
                ),
            )

    # 買ってほしいものを登録する
    for memo in DEMO_MEMOS:
        connection.execute(
            """
            INSERT INTO shopping_memos (text)
            VALUES (%s)
            """,
            (memo,),
        )


def main():
    """見本データの登録処理を実行する。"""

    # 既存の環境変数を上書きせず、.envから不足分を読み込む
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        print(
            "DATABASE_URLが設定されていません。.envまたは環境変数を確認してください。"
        )
        return 1

    try:
        host, database_name = get_database_target(database_url)
    except ValueError:
        print("DATABASE_URLの形式を確認できません。接続先の設定を確認してください。")
        return 1

    # yes以外ならDB接続・変更を行わない
    if not confirm_data_replacement(host, database_name):
        return 0

    try:
        # このwithブロック全体が1つのトランザクションになる
        with get_connection_context() as connection:
            if not tables_exist(connection):
                print(
                    "テーブルがありません。"
                    "先にアプリを一度起動して、"
                    "テーブルを作成してください。"
                )
                return 1

            insert_demo_data(connection)

        # withを正常に抜けた時点でトランザクションが確定する
        print("見本データを入れました。")
        print(f"品目: {len(DEMO_ITEMS)}件")
        print(f"消費量: {len(DEMO_ITEMS) * len(CONSUMPTION_DAYS)}件")
        print(f"買ってほしいもの: {len(DEMO_MEMOS)}件")

        return 0

    except (psycopg.Error, RuntimeError):
        # 接続情報やDBの詳細を出さず、日本語のメッセージで終了する
        print(
            "データベースへの接続または処理に失敗しました。"
            "接続先設定とDBの状態を確認してください。"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
