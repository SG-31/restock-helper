from validation import validate_stock, validate_item_form


# =========================
# validate_stock
# =========================


def test_validate_stock_zero_returns_zero():
    # 在庫数0は有効な値として受け付ける
    result, error = validate_stock("0")

    assert result == 0
    assert error is None


def test_validate_stock_negative_returns_error():
    # 在庫数は0以上で入力する
    result, error = validate_stock("-1")

    assert result is None
    assert error == "在庫数は0以上で入力してください。"


def test_validate_stock_9999_returns_9999():
    # 在庫数9999は上限値として受け付ける
    result, error = validate_stock("9999")

    assert result == 9999
    assert error is None


def test_validate_stock_10000_returns_error():
    # 在庫数は9999以下で入力する
    result, error = validate_stock("10000")

    assert result is None
    assert error == "在庫数は9999以下で入力してください。"


def test_validate_stock_non_integer_returns_error():
    # 在庫数は整数で入力する
    result, error = validate_stock("abc")

    assert result is None
    assert error == "在庫数は整数で入力してください。"


def test_validate_stock_returns_integer_not_string():
    # 入力値が文字列でも、検証後の在庫数は整数として返す
    result, error = validate_stock("10")

    assert result == 10
    assert isinstance(result, int)
    assert error is None


# =========================
# validate_item_form
# =========================


def test_validate_item_form_valid_input_returns_data():
    # 正常な入力の場合は、入力データとNoneを返す
    form = {
        "name": "牛乳",
        "unit": "本",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result == {
        "name": "牛乳",
        "unit": "本",
        "current_stock": 5,
    }
    assert error is None


def test_validate_item_form_strips_name_whitespace():
    # 品目名の前後の空白は取り除いてから扱う
    form = {
        "name": " 牛乳 ",
        "unit": "本",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result["name"] == "牛乳"
    assert error is None


def test_validate_item_form_blank_name_returns_error():
    # 品目名が空欄の場合はエラーとする
    form = {
        "name": "",
        "unit": "本",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "品目名を入力してください。"


def test_validate_item_form_spaces_only_name_returns_error():
    # 品目名が空白だけの場合も空欄として扱う
    form = {
        "name": "   ",
        "unit": "本",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "品目名を入力してください。"


def test_validate_item_form_name_100_chars_is_valid():
    # 品目名100文字は上限値として受け付ける
    form = {
        "name": "A" * 100,
        "unit": "個",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is not None
    assert len(result["name"]) == 100
    assert error is None


def test_validate_item_form_name_101_chars_returns_error():
    # 品目名101文字は上限を超えるためエラーとする
    form = {
        "name": "A" * 101,
        "unit": "個",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "品目名は100文字以内で入力してください。"


def test_validate_item_form_blank_unit_returns_error():
    # 単位が空欄の場合はエラーとする
    form = {
        "name": "牛乳",
        "unit": "",
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "単位を入力してください。"


def test_validate_item_form_unit_100_chars_is_valid():
    # 単位100文字は上限値として受け付ける
    form = {
        "name": "牛乳",
        "unit": "A" * 100,
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is not None
    assert len(result["unit"]) == 100
    assert error is None


def test_validate_item_form_unit_101_chars_returns_error():
    # 単位101文字は上限を超えるためエラーとする
    form = {
        "name": "牛乳",
        "unit": "A" * 101,
        "current_stock": "5",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "単位は100文字以内で入力してください。"


def test_validate_item_form_blank_stock_returns_error():
    # 在庫数が空欄の場合はエラーとする
    form = {
        "name": "牛乳",
        "unit": "本",
        "current_stock": "",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "在庫数を入力してください。"


def test_validate_item_form_negative_stock_returns_error():
    # 在庫数の検証はvalidate_stockのルールに従う
    form = {
        "name": "牛乳",
        "unit": "本",
        "current_stock": "-1",
    }

    result, error = validate_item_form(form)

    assert result is None
    assert error == "在庫数は0以上で入力してください。"
