import sqlite3
from flask import Blueprint, render_template, request, redirect
import db


shopping_bp = Blueprint("shopping", __name__)


@shopping_bp.route("/list")
def shopping_list():
    try:
        # DB接続はコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 補充が必要な品目を共通処理から取得する
            shopping_items = db.get_shopping_list(connection)
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
                memos=memos,
            )

    except sqlite3.Error as error:
        print(f"買い物リストの取得エラー: {error}")
        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買い物リストを取得できませんでした。DBエラー: {error}",
        )


@shopping_bp.route("/list/memo", methods=["POST"])
def add_memo():
    text = request.form.get("text", "").strip()

    if not text:
        return redirect("/list")

    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            connection.execute(
                """
                INSERT INTO shopping_memos (text)
                VALUES (?)
                """,
                (text,),
            )

            return redirect("/list")

    except sqlite3.Error as error:
        print(f"買ってほしいものの登録エラー: {error}")
        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買ってほしいものを登録できませんでした。DBエラー: {error}",
        )


@shopping_bp.route("/list/memo/<int:memo_id>/delete", methods=["POST"])
def delete_memo(memo_id):
    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            cursor = connection.execute(
                """
                DELETE FROM shopping_memos
                WHERE id = ?
                """,
                (memo_id,),
            )

            if cursor.rowcount == 0:
                return "買ってほしいものが見つかりません。", 404

            return redirect("/list")

    except sqlite3.Error as error:
        print(f"買ってほしいものの削除エラー: {error}")
        return render_template(
            "list.html",
            shopping_items=[],
            memos=[],
            error=f"買ってほしいものを削除できませんでした。DBエラー: {error}",
        )


@shopping_bp.route("/input/complete", methods=["POST"])
def complete_shopping():
    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 現在の補充必要数を共通処理から取得する
            shopping_items = db.get_shopping_list(connection)

            # 補充必要数を現在庫に加算する
            for item in shopping_items:
                connection.execute(
                    """
                    UPDATE items
                    SET current_stock = current_stock + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (item["restock_amount"], item["id"]),
                )

            # 買い物リストのメモをすべて削除する
            connection.execute(
                """
                DELETE FROM shopping_memos
                """
            )

            return redirect("/input")

    except sqlite3.Error as error:
        print(f"買い物完了処理のエラー: {error}")
        return f"買い物完了処理に失敗しました。DBエラー: {error}", 500
