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