from calculations import (
    calc_moving_average,
    calc_required_quantity,
    calc_restock_info,
)


# =========================
# calc_moving_average
# =========================


def test_calc_moving_average_empty_returns_none():
    # decisions.md 3-9：消費量データが0件の場合は計算対象外
    result = calc_moving_average([])

    assert result is None


def test_calc_moving_average_one_value_returns_same_value():
    # decisions.md 3：データが4回未満なら、存在するデータだけで平均する
    result = calc_moving_average([5])

    assert result == 5


def test_calc_moving_average_multiple_values_returns_average():
    # decisions.md 3：週間消費量の平均を計算する
    result = calc_moving_average([1, 2, 3])

    assert result == 2


def test_calc_moving_average_four_values_returns_average():
    # decisions.md 3：直近4週間分の週間消費量を平均する
    result = calc_moving_average([1, 2, 3, 4])

    assert result == 2.5


def test_calc_moving_average_includes_zero():
    # decisions.md 3-2：消費量0は移動平均の計算に含める
    result = calc_moving_average([0, 2])

    assert result == 1


# =========================
# calc_required_quantity
# =========================


def test_calc_required_quantity_none_average_returns_zero():
    # decisions.md 3-9：消費量データがない場合は補充計算を行わない
    result = calc_required_quantity(None, 10)

    assert result == 0


def test_calc_required_quantity_average_two_stock_zero_returns_three():
    # decisions.md 3：適正在庫数＝移動平均×1.5、補充必要数は適正在庫数−現在庫数
    result = calc_required_quantity(2, 0)

    assert result == 3


def test_calc_required_quantity_rounds_up_decimal():
    # decisions.md 3-8：補充必要数に小数が生じる場合は切り上げる
    result = calc_required_quantity(3, 1)

    assert result == 4


def test_calc_required_quantity_stock_equal_appropriate_returns_zero():
    # decisions.md 3：現在庫が適正在庫数以上なら補充必要数は0
    result = calc_required_quantity(2, 3)

    assert result == 0


def test_calc_required_quantity_one_below_appropriate_returns_one():
    # decisions.md 3：適正在庫数3、現在庫2の場合の補充必要数は1
    result = calc_required_quantity(2, 2)

    assert result == 1


def test_calc_required_quantity_excessive_stock_returns_zero():
    # decisions.md 3：補充必要数がマイナスになる場合は0とする
    result = calc_required_quantity(1, 10)

    assert result == 0


def test_calc_required_quantity_uses_moving_average_result():
    # decisions.md 3：移動平均の計算結果を補充必要数の計算に使用する
    moving_average = calc_moving_average([1, 1, 2])
    result = calc_required_quantity(moving_average, 0)

    assert result == 2


# =========================
# calc_restock_info
# =========================


def test_calc_restock_info_no_consumption_returns_none():
    # decisions.md 3-9：消費量データが0件なら買い物リストの計算対象外
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [])

    assert result is None


def test_calc_restock_info_no_replenishment_returns_none():
    # decisions.md 9-10：補充必要数が0以下なら買い物リストに表示しない
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 10,
    }

    result = calc_restock_info(item, [1, 1])

    assert result is None


def test_calc_restock_info_all_zero_consumption_returns_none():
    # decisions.md 3-2：消費量0を平均に含め、補充不要なら対象外とする
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [0, 0])

    assert result is None


def test_calc_restock_info_returns_expected_keys():
    # decisions.md 8-6：補充情報はid、name、unit、restock_amountを返す
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [2, 2])

    assert set(result.keys()) == {
        "id",
        "name",
        "unit",
        "restock_amount",
    }


def test_calc_restock_info_returns_expected_values():
    # decisions.md 3：平均2×1.5＝適正在庫3、現在庫0なので補充数は3
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [2, 2])

    assert result == {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "restock_amount": 3,
    }


def test_calc_restock_info_uses_restock_amount_key():
    # decisions.md 8-6：補充数量のキー名はrestock_amount
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [2, 2])

    assert "restock_amount" in result


def test_calc_restock_info_does_not_use_required_quantity_key():
    # decisions.md 8-6：補充数量のキー名はrequired_quantityではない
    item = {
        "id": 1,
        "name": "牛乳",
        "unit": "本",
        "current_stock": 0,
    }

    result = calc_restock_info(item, [2, 2])

    assert "required_quantity" not in result
