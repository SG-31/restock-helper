import psycopg
from flask import Blueprint, render_template, request, flash, redirect
from validation import validate_stock
import db


stock_bp = Blueprint("stock", __name__)


# =========================
# 在庫入力
# =========================
@stock_bp.route("/input", methods=["GET", "POST"])
def stock_input():
    try:
        # DB接続はコンテキストマネージャで管理する
        with db.get_connection_context() as connection:
            # -------------------------
            # 管理品目を取得
            # -------------------------
            items = db.get_items(connection)

            # 管理品目が0件の場合
            if not items:
                return render_template(
                    "input.html",
                    items=[],
                    shopping_list=[],
                    error="管理品目が登録されていません。",
                )

            # -------------------------
            # GET：入力画面を表示
            # -------------------------
            if request.method == "GET":
                shopping_list = db.get_shopping_list(connection)

                return render_template(
                    "input.html",
                    items=items,
                    shopping_list=shopping_list,
                )

            # -------------------------
            # POST：在庫を更新
            # -------------------------
            warnings = []
            updated_count = 0

            for item in items:
                field_name = f"stock_{item['id']}"
                stock_text = request.form.get(field_name, "").strip()

                # 空欄はスキップ
                if stock_text == "":
                    continue

                # 在庫数の検証は共通関数に任せる
                current_stock, error = validate_stock(stock_text)

                if error:
                    warnings.append(f"{item['name']}：{error}")
                    continue

                # -------------------------
                # 前回値を取得
                # -------------------------
                previous_stock = item["current_stock"]

                # 週間消費量を計算
                consumption = max(0, previous_stock - current_stock)

                # 消費量を保存
                connection.execute(
                    """
                    INSERT INTO consumptions
                        (item_id, consumption)
                    VALUES (%s, %s)
                    """,
                    (item["id"], consumption),
                )

                # 現在庫数を更新
                connection.execute(
                    """
                    UPDATE items
                    SET current_stock = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (current_stock, item["id"]),
                )

                # 実際に保存した品目数をカウント
                updated_count += 1

            # -------------------------
            # Flashメッセージを登録
            # -------------------------
            if updated_count > 0:
                flash("在庫を更新しました。")
            else:
                flash("更新された品目はありませんでした。")

            for warning in warnings:
                flash(warning, "warning")

            # POST処理完了後はGETへリダイレクトする
            return redirect("/input")

    except psycopg.Error as error:
        print(f"在庫入力のDBエラー: {error}")

        # GET時の読み込み失敗ではリダイレクトを繰り返さず、共通メッセージを表示する
        if request.method == "GET":
            return render_template(
                "input.html",
                items=[],
                shopping_list=[],
                error="データを読み込めませんでした。時間をおいて開き直してください。",
            )

        # POST時は従来どおりFlashで通知してGETへリダイレクトする（PRG）
        flash(
            "在庫を更新できませんでした。しばらくしてから、もう一度お試しください。",
            "error",
        )

        return redirect("/input")
