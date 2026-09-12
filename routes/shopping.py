from flask import Blueprint, render_template, request, redirect
import sqlite3

import db
from calculations import calc_moving_average, calc_required_quantity


shopping_bp = Blueprint("shopping", __name__)


def get_shopping_items(connection):
    """補充が必要な管理品目を計算して返す。"""

    items = connection.execute(
        """
        SELECT id, name, unit, current_stock
        FROM items
        ORDER BY id
        """
    ).fetchall()

    shopping_items = []

    for item in items:
        consumptions = connection.execute(
            """
            SELECT consumption
            FROM consumptions
            WHERE item_id = ?
            ORDER BY recorded_at DESC
            LIMIT 4
            """,
            (item["id"],)
        ).fetchall()

        consumption_values = [
            consumption["consumption"]
            for consumption in consumptions
        ]

        moving_average = calc_moving_average(consumption_values)

        required_quantity = calc_required_quantity(
            moving_average,
            item["current_stock"]
        )

        if required_quantity > 0:
            shopping_items.append(
                {
                    "name": item["name"],
                    "unit": item["unit"],
                    "required_quantity": required_quantity
                }
            )

    return shopping_items


@shopping_bp.route("/list")
def shopping_list():
    connection = None

    try:
        connection = db.get_connection()

        shopping_items = get_shopping_items(connection)

        memos = connection.execute(
            """
            SELECT id, text
            FROM shopping_memos
            ORDER BY id
            """
        ).fetchall()

        return render_template(
            "list.html",
            shopping_items=shopping_items,
            memos=memos
        )

    except sqlite3.Error as error:
        print(f"買い物リストの取得エラー: {error}")

        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買い物リストを取得できませんでした。DBエラー: {error}"
        )

    finally:
        if connection is not None:
            connection.close()


@shopping_bp.route("/list/memo", methods=["POST"])
def add_memo():
    text = request.form.get("text", "").strip()

    if not text:
        return redirect("/list")

    connection = None

    try:
        connection = db.get_connection()

        connection.execute(
            """
            INSERT INTO shopping_memos (text)
            VALUES (?)
            """,
            (text,)
        )

        connection.commit()

        return redirect("/list")

    except sqlite3.Error as error:
        print(f"買ってほしいものの登録エラー: {error}")

        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買ってほしいものを登録できませんでした。DBエラー: {error}"
        )

    finally:
        if connection is not None:
            connection.close()


@shopping_bp.route("/list/memo/<int:memo_id>/delete", methods=["POST"])
def delete_memo(memo_id):
    connection = None

    try:
        connection = db.get_connection()

        cursor = connection.execute(
            """
            DELETE FROM shopping_memos
            WHERE id = ?
            """,
            (memo_id,)
        )

        if cursor.rowcount == 0:
            return "買ってほしいものが見つかりません。", 404

        connection.commit()

        return redirect("/list")

    except sqlite3.Error as error:
        print(f"買ってほしいものの削除エラー: {error}")

        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買ってほしいものを削除できませんでした。DBエラー: {error}"
        )

    finally:
        if connection is not None:
            connection.close()


@shopping_bp.route("/input/complete", methods=["POST"])
def complete_shopping():
    connection = None

    try:
        connection = db.get_connection()

        items = connection.execute(
            """
            SELECT id, current_stock
            FROM items
            ORDER BY id
            """
        ).fetchall()

        for item in items:
            consumptions = connection.execute(
                """
                SELECT consumption
                FROM consumptions
                WHERE item_id = ?
                ORDER BY recorded_at DESC
                LIMIT 4
                """,
                (item["id"],)
            ).fetchall()

            consumption_values = [
                consumption["consumption"]
                for consumption in consumptions
            ]

            moving_average = calc_moving_average(
                consumption_values
            )

            required_quantity = calc_required_quantity(
                moving_average,
                item["current_stock"]
            )

            if required_quantity > 0:
                connection.execute(
                    """
                    UPDATE items
                    SET current_stock = current_stock + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (required_quantity, item["id"])
                )

        connection.execute(
            """
            DELETE FROM shopping_memos
            """
        )

        connection.commit()

        return redirect("/input")

    except sqlite3.Error as error:
        print(f"買い物完了処理のエラー: {error}")

        return f"買い物完了処理に失敗しました。DBエラー: {error}", 500

    finally:
        if connection is not None:
            connection.close()