import sqlite3

from flask import Blueprint, render_template, request, redirect

import db


items_bp = Blueprint("items", __name__)


# =========================
# 管理品目一覧
# =========================

@items_bp.route("/items")
def items():
    connection = None

    try:
        # DBに接続
        connection = db.get_connection()

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

@items_bp.route("/items/new", methods=["GET", "POST"])
def new_item():

    # GETの場合：登録フォームを表示する
    if request.method == "GET":
        return render_template(
            "item_form.html",
            action_url="/items/new"
        )

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
        connection = db.get_connection()

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

@items_bp.route(
    "/items/<int:item_id>/edit",
    methods=["GET", "POST"]
)
def edit_item(item_id):

    connection = None

    try:
        # DBに接続
        connection = db.get_connection()

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
# 管理品目削除
# =========================

@items_bp.route(
    "/items/<int:item_id>/delete",
    methods=["POST"]
)
def delete_item(item_id):
    """指定された管理品目を削除する。"""

    connection = None

    try:
        # DBに接続
        connection = db.get_connection()

        # 指定されたIDの品目が存在するか確認
        cursor = connection.execute(
            """
            SELECT id
            FROM items
            WHERE id = ?
            """,
            (item_id,)
        )

        item = cursor.fetchone()

        # 指定されたIDの品目が存在しない場合
        if item is None:
            return "品目が見つかりません。", 404

        # 管理品目を削除
        # ON DELETE CASCADEにより、紐づくconsumptionsも削除される
        connection.execute(
            """
            DELETE FROM items
            WHERE id = ?
            """,
            (item_id,)
        )

        # 削除を確定
        connection.commit()

        # 管理品目一覧へ戻る
        return redirect("/items")

    except sqlite3.Error as error:
        print(f"管理品目の削除エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error=f"管理品目を削除できませんでした。DBエラー: {error}"
        )

    finally:
        # DB接続ができていた場合は必ず閉じる
        if connection is not None:
            connection.close()