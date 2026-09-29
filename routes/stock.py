import sqlite3

from flask import Blueprint, render_template, request

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
                return render_template(
                    "input.html",
                    items=items,
                    shopping_list=[],
                )

            # -------------------------
            # POST：在庫を更新
            # -------------------------
            warnings = []

            for item in items:
                field_name = f"stock_{item['id']}"
                stock_text = request.form.get(field_name, "").strip()

                # 空欄はスキップ
                if stock_text == "":
                    continue

                # 整数に変換
                try:
                    current_stock = int(stock_text)
                except ValueError:
                    warnings.append(f"{item['name']}：在庫数は整数で入力してください。")
                    continue

                # マイナス値は保存しない
                if current_stock < 0:
                    warnings.append(
                        f"{item['name']}：在庫数は0以上で入力してください。"
                    )
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
                    VALUES (?, ?)
                    """,
                    (item["id"], consumption),
                )

                # 現在庫数を更新
                connection.execute(
                    """
                    UPDATE items
                    SET current_stock = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (current_stock, item["id"]),
                )

            # -------------------------
            # 更新後の品目を再取得
            # -------------------------
            updated_items = db.get_items(connection)

            # -------------------------
            # 更新後の買い物リストを取得
            # -------------------------
            shopping_list = db.get_shopping_list(connection)

            return render_template(
                "input.html",
                items=updated_items,
                shopping_list=shopping_list,
                message="在庫を更新しました。",
                warnings=warnings,
            )

    except sqlite3.Error as error:
        # DBエラーは握りつぶさず表示する
        print(f"在庫入力のDBエラー: {error}")

        return render_template(
            "input.html",
            items=[],
            shopping_list=[],
            error=f"在庫を更新できませんでした。DBエラー: {error}",
        )
