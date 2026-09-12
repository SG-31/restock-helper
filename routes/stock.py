import sqlite3
from flask import Blueprint, render_template, request
import db
from calculations import calc_moving_average, calc_required_quantity


stock_bp = Blueprint("stock", __name__)


# =========================
# 消費量を取得
# =========================
def get_consumptions(connection, item_id):
    """
    指定した品目の直近4件の消費量を取得する。
    """
    cursor = connection.execute(
        """
        SELECT consumption
        FROM consumptions
        WHERE item_id = ?
        ORDER BY recorded_at DESC
        LIMIT 4
        """,
        (item_id,)
    )

    return cursor.fetchall()


# =========================
# 買い物リストを作成
# =========================
def get_shopping_list(connection):
    """
    全管理品目について補充必要数を計算し、
    補充が必要な品目だけを返す。
    """
    cursor = connection.execute(
        """
        SELECT id, name, unit, current_stock
        FROM items
        ORDER BY id
        """
    )
    items = cursor.fetchall()

    shopping_list = []

    for item in items:
        consumptions = get_consumptions(
            connection,
            item["id"]
        )

        # 消費量データがない場合は対象外
        if not consumptions:
            continue

        consumption_values = [
            row["consumption"]
            for row in consumptions
        ]

        moving_average = calc_moving_average(
            consumption_values
        )

        restock_amount = calc_required_quantity(
            moving_average,
            item["current_stock"]
        )

        # 補充必要数が0より大きい場合だけ表示
        if restock_amount > 0:
            shopping_list.append(
                {
                    "name": item["name"],
                    "unit": item["unit"],
                    "restock_amount": restock_amount
                }
            )

    return shopping_list


# =========================
# 在庫入力
# =========================
@stock_bp.route("/input", methods=["GET", "POST"])
def stock_input():
    connection = None

    try:
        # DB接続は共通関数を使用する
        connection = db.get_connection()

        # -------------------------
        # 管理品目を取得
        # -------------------------
        cursor = connection.execute(
            """
            SELECT id, name, unit, current_stock
            FROM items
            ORDER BY id
            """
        )
        items = cursor.fetchall()

        # 管理品目が0件の場合
        if not items:
            return render_template(
                "input.html",
                items=[],
                shopping_list=[],
                error="管理品目が登録されていません。"
            )

        # -------------------------
        # GET：入力画面を表示
        # -------------------------
        if request.method == "GET":
            return render_template(
                "input.html",
                items=items,
                shopping_list=[]
            )

        # -------------------------
        # POST：在庫を更新
        # -------------------------
        warnings = []

        for item in items:
            field_name = f"stock_{item['id']}"
            stock_text = request.form.get(
                field_name,
                ""
            ).strip()

            # 空欄はスキップ
            if stock_text == "":
                continue

            # 整数に変換
            try:
                current_stock = int(stock_text)
            except ValueError:
                warnings.append(
                    f"{item['name']}：在庫数は整数で入力してください。"
                )
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
            consumption = max(
                0,
                previous_stock - current_stock
            )

            # 消費量を保存
            connection.execute(
                """
                INSERT INTO consumptions
                    (item_id, consumption)
                VALUES (?, ?)
                """,
                (item["id"], consumption)
            )

            # 現在庫数を更新
            connection.execute(
                """
                UPDATE items
                SET current_stock = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (current_stock, item["id"])
            )

        # 正常な更新を確定
        connection.commit()

        # -------------------------
        # 更新後の品目を再取得
        # -------------------------
        cursor = connection.execute(
            """
            SELECT id, name, unit, current_stock
            FROM items
            ORDER BY id
            """
        )
        updated_items = cursor.fetchall()

        # -------------------------
        # 更新後の買い物リストを計算
        # -------------------------
        shopping_list = get_shopping_list(connection)

        return render_template(
            "input.html",
            items=updated_items,
            shopping_list=shopping_list,
            message="在庫を更新しました。",
            warnings=warnings
        )

    except sqlite3.Error as error:
        # DBエラーは握りつぶさず表示する
        print(f"在庫入力のDBエラー: {error}")

        if connection is not None:
            connection.rollback()

        return render_template(
            "input.html",
            items=[],
            shopping_list=[],
            error=f"在庫を更新できませんでした。DBエラー: {error}"
        )

    finally:
        # DB接続ができていた場合は必ず閉じる
        if connection is not None:
            connection.close()