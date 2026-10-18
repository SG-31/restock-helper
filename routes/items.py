import psycopg
from flask import Blueprint, render_template, request, redirect, flash
from validation import validate_item_form
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

    except psycopg.Error as error:
        print(f"管理品目一覧の取得エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error="データを読み込めませんでした。時間をおいて開き直してください。",
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
    # 送信された値をフォームに残すために保持する
    form_data = {
        "name": request.form.get("name", ""),
        "unit": request.form.get("unit", ""),
        "current_stock": request.form.get("current_stock", ""),
    }

    # フォーム入力を共通関数で検証する
    validated_data, error = validate_item_form(request.form)

    if error:
        return render_template(
            "item_form.html",
            form_data=form_data,
            item=None,
            action_url="/items/new",
            error=error,
        )

    try:
        with db.get_connection_context() as connection:
            # 品目名の重複を確認
            if db.item_name_exists(connection, validated_data["name"]):
                return render_template(
                    "item_form.html",
                    form_data=form_data,
                    item=None,
                    action_url="/items/new",
                    error="同じ品目名がすでに登録されています。",
                )

            # 管理品目を登録する
            connection.execute(
                """
                INSERT INTO items (name, unit, current_stock)
                VALUES (%s, %s, %s)
                """,
                (
                    validated_data["name"],
                    validated_data["unit"],
                    validated_data["current_stock"],
                ),
            )

        # 登録情報をFlashに保存して一覧画面へ移動する
        flash("管理品目を登録しました。")
        return redirect("/items")

    except psycopg.IntegrityError:
        # UNIQUE制約などによる重複エラー
        return render_template(
            "item_form.html",
            form_data=form_data,
            item=None,
            action_url="/items/new",
            error="同じ品目名がすでに登録されています。",
        )

    except psycopg.Error as error:
        print(f"管理品目の登録エラー：{error}")

        return render_template(
            "item_form.html",
            form_data=form_data,
            item=None,
            action_url="/items/new",
            error="管理品目を登録できませんでした。しばらくしてから、もう一度お試しください。",
        )


# =========================
# 管理品目編集
# =========================


@items_bp.route(
    "/items/<int:item_id>/edit",
    methods=["GET", "POST"],
)
def edit_item(item_id):

    item = None
    form_data = None

    try:
        # DB接続とトランザクションをコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # 指定されたIDの管理品目を取得
            item = db.get_item(connection, item_id)

            # 指定されたIDの品目が存在しない場合
            if item is None:
                return render_template("404.html"), 404

            # GETの場合：現在の値をフォームに表示する
            if request.method == "GET":
                return render_template(
                    "item_form.html",
                    item=item,
                    action_url=f"/items/{item_id}/edit",
                )

            # 送信された値をフォームに残すために保持する
            form_data = {
                "name": request.form.get("name", ""),
                "unit": request.form.get("unit", ""),
                "current_stock": request.form.get("current_stock", ""),
            }

            # フォーム入力を共通関数で検証する
            validated_data, error = validate_item_form(request.form)

            if error:
                return render_template(
                    "item_form.html",
                    item=item,
                    form_data=form_data,
                    action_url=f"/items/{item_id}/edit",
                    error=error,
                )

            # 品目名の重複チェック
            if db.item_name_exists(
                connection,
                validated_data["name"],
                item_id,
            ):
                return render_template(
                    "item_form.html",
                    item=item,
                    form_data=form_data,
                    action_url=f"/items/{item_id}/edit",
                    error="同じ品目名がすでに登録されています。",
                )

            # 管理品目を更新する
            connection.execute(
                """
                UPDATE items
                SET name = %s,
                    unit = %s,
                    current_stock = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    validated_data["name"],
                    validated_data["unit"],
                    validated_data["current_stock"],
                    item_id,
                ),
            )

        # 更新成功をFlashに保存して一覧画面へ移動する
        flash("管理品目を変更しました。")
        return redirect("/items")

    except psycopg.IntegrityError:
        # UNIQUE制約などによる重複エラー
        return render_template(
            "item_form.html",
            item=item,
            form_data=form_data,
            action_url=f"/items/{item_id}/edit",
            error="同じ品目名がすでに登録されています。",
        )

    except psycopg.Error as error:
        if request.method == "GET":
            print(f"管理品目の取得エラー: {error}")
            # 読み込みに失敗した場合、空の編集フォームを誤って表示しない
            return render_template(
                "item_form.html",
                item=None,
                form_data=None,
                action_url=f"/items/{item_id}/edit",
                is_edit=True,
                load_error=True,
                error="データを読み込めませんでした。時間をおいて開き直してください。",
            )

        print(f"管理品目の変更エラー: {error}")

        return render_template(
            "item_form.html",
            item=item,
            form_data=form_data,
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
                return render_template("404.html"), 404

            # 管理品目を削除
            # ON DELETE CASCADEにより、紐づくconsumptionsも削除される
            connection.execute(
                """
                DELETE FROM items
                WHERE id = %s
                """,
                (item_id,),
            )

            # 管理品目一覧へ戻る
            return redirect("/items")

    except psycopg.Error as error:
        print(f"管理品目の削除エラー: {error}")

        return render_template(
            "items.html",
            items=[],
            error="管理品目を削除できませんでした。しばらくしてから、もう一度お試しください。",
        )
