def validate_stock(stock_text):
    """在庫数が整数かつ0以上9999以下か検証する。"""
    try:
        stock = int(stock_text)
    except ValueError:
        return None, "在庫数は整数で入力してください。"

    if stock < 0:
        return None, "在庫数は0以上で入力してください。"

    if stock > 9999:
        return None, "在庫数は9999以下で入力してください。"

    return stock, None


def validate_item_form(form):
    """管理品目の登録・変更フォームを検証する。"""

    name = form.get("name", "").strip()
    unit = form.get("unit", "").strip()
    stock_text = form.get("current_stock", "").strip()

    # 品目名のチェック
    if not name:
        return None, "品目名を入力してください。"

    if len(name) > 100:
        return None, "品目名は100文字以内で入力してください。"

    # 単位のチェック
    if not unit:
        return None, "単位を入力してください。"

    if len(unit) > 100:
        return None, "単位は100文字以内で入力してください。"

    # 在庫数のチェック
    if not stock_text:
        return None, "在庫数を入力してください。"

    current_stock, error = validate_stock(stock_text)

    if error:
        return None, error

    return {
        "name": name,
        "unit": unit,
        "current_stock": current_stock,
    }, None
