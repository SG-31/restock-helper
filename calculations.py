import math


def calc_moving_average(consumptions):
    """直近の週間消費量から移動平均を計算する。

    消費量データがない場合は、計算対象外としてNoneを返す。
    """
    if not consumptions:
        return None

    return sum(consumptions) / len(consumptions)


def calc_required_quantity(moving_average, current_stock):
    """移動平均と現在庫数から補充必要数を計算する。"""
    if moving_average is None:
        return 0

    appropriate_stock = moving_average * 1.5
    required = appropriate_stock - current_stock

    # 補充が必要な場合は、必要数を整数に切り上げる。
    return math.ceil(max(0, required))


def calc_restock_info(item, consumption_values):
    """品目情報と消費量から補充情報をまとめて計算する。"""
    moving_average = calc_moving_average(consumption_values)

    # 消費量データがない品目は計算対象外とする
    if moving_average is None:
        return None

    required_quantity = calc_required_quantity(
        moving_average,
        item["current_stock"],
    )

    # 補充不要な品目は買い物リストに追加しない
    if required_quantity <= 0:
        return None

    return {
        "id": item["id"],
        "name": item["name"],
        "unit": item["unit"],
        "restock_amount": required_quantity,
    }
