import sqlite3

from flask import Blueprint, render_template, request, redirect

import db


items_bp = Blueprint("items", __name__)


# =========================
# 管理品目一覧
# =========================


@items_bp.route("/items")
def items():
    try:
        # DB接続はコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 管理品目を共通関数から取得する
            items = db.get_items(connection)

            # HTMLにitemsを渡す
            return render_template("items.html", items=items)

    except sqlite3.Error as error:
        print(f"管理品目一覧の取得エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error="管理品目一覧を取得できませんでした。しばらくしてから、もう一度お試しください。",
        )


# =========================
# 管理品目登録
# =========================


@items_bp.route("/items/new", methods=["GET", "POST"])
def new_item():

    # GETの場合：登録フォームを表示する
    if request.method == "GET":
        return render_template(
            "item_form.html",
            action_url="/items/new",
        )

    # POSTの場合：フォームから送信されたデータを保存する
    name = request.form.get("name", "").strip()
    unit = request.form.get("unit", "").strip()
    stock_text = request.form.get("current_stock", "").strip()

    # 品目名・単位の入力チェック
    for field_value, field_label in [(name, "品目名"), (unit, "単位")]:
        if not field_value:
            return render_template(
                "item_form.html",
                error=f"{field_label}を入力してください。",
                action_url="/items/new",
            )

        if len(field_value) > 100:
            return render_template(
                "item_form.html",
                error=f"{field_label}は100文字以内で入力してください。",
                action_url="/items/new",
            )

    # 初期在庫数を整数に変換する
    try:
        current_stock = int(stock_text)

    except ValueError:
        return render_template(
            "item_form.html",
            error="初期在庫数は整数で入力してください。",
            action_url="/items/new",
        )

    # 初期在庫数がマイナスの場合は保存しない
    if current_stock < 0:
        return render_template(
            "item_form.html",
            error="初期在庫数は0以上で入力してください。",
            action_url="/items/new",
        )

    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # itemsテーブルに新しい品目を登録
            connection.execute(
                """
                INSERT INTO items (name, unit, current_stock)
                VALUES (?, ?, ?)
                """,
                (name, unit, current_stock),
            )

            return render_template(
                "item_form.html",
                message="管理品目を登録しました。",
                action_url="/items/new",
            )

    except sqlite3.Error as error:
        print(f"管理品目の登録エラー: {error}")

        return render_template(
            "item_form.html",
            error="管理品目を登録できませんでした。しばらくしてから、もう一度お試しください。",
            action_url="/items/new",
        )


# =========================
# 管理品目編集
# =========================


@items_bp.route(
    "/items/<int:item_id>/edit",
    methods=["GET", "POST"],
)
def edit_item(item_id):

    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 指定されたIDの管理品目を取得
            item = db.get_item(connection, item_id)

            # 指定されたIDの品目が存在しない場合
            if item is None:
                return "品目が見つかりません。", 404

            # GETの場合：現在の値をフォームに表示する
            if request.method == "GET":
                return render_template(
                    "item_form.html",
                    item=item,
                    action_url=f"/items/{item_id}/edit",
                )

            # POSTの場合：フォームから送信されたデータを取得
            name = request.form.get("name", "").strip()
            unit = request.form.get("unit", "").strip()
            stock_text = request.form.get("current_stock", "").strip()

            # 品目名・単位の入力チェック
            for field_value, field_label in [(name, "品目名"), (unit, "単位")]:
                if not field_value:
                    return render_template(
                        "item_form.html",
                        item=item,
                        action_url=f"/items/{item_id}/edit",
                        error=f"{field_label}を入力してください。",
                    )

                if len(field_value) > 100:
                    return render_template(
                        "item_form.html",
                        item=item,
                        action_url=f"/items/{item_id}/edit",
                        error=f"{field_label}は100文字以内で入力してください。",
                    )

            # 現在庫数を整数に変換する
            try:
                current_stock = int(stock_text)

            except ValueError:
                return render_template(
                    "item_form.html",
                    item=item,
                    action_url=f"/items/{item_id}/edit",
                    error="現在庫数は整数で入力してください。",
                )

            # 現在庫数がマイナスの場合は更新しない
            if current_stock < 0:
                return render_template(
                    "item_form.html",
                    item=item,
                    action_url=f"/items/{item_id}/edit",
                    error="現在庫数は0以上で入力してください。",
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
                (name, unit, current_stock, item_id),
            )

            # 更新後の値を取得
            updated_item = db.get_item(connection, item_id)

            return render_template(
                "item_form.html",
                item=updated_item,
                action_url=f"/items/{item_id}/edit",
                message="管理品目を変更しました。",
            )

    except sqlite3.Error as error:
        print(f"管理品目の変更エラー: {error}")

        return render_template(
            "item_form.html",
            item=None,
            action_url=f"/items/{item_id}/edit",
            error="管理品目を変更できませんでした。しばらくしてから、もう一度お試しください。",
        )


# =========================
# 管理品目削除
# =========================


@items_bp.route(
    "/items/<int:item_id>/delete",
    methods=["POST"],
)
def delete_item(item_id):
    """指定された管理品目を削除する。"""

    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 指定されたIDの品目が存在するか確認
            item = db.get_item(connection, item_id)

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
                (item_id,),
            )

            # 管理品目一覧へ戻る
            return redirect("/items")

    except sqlite3.Error as error:
        print(f"管理品目の削除エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error="管理品目を削除できませんでした。しばらくしてから、もう一度お試しください。",
        )
