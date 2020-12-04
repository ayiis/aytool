import q
import re
import math
"""

每 0.05 补到 0.025
每 0.06 补到 0.03

b = 10000
r = 0.06
t = 6

总计： b ** r
损失: (1 - (0.06)) ** 6 - 1

"""


def printf(strf, paras):
    """
        打印 2 位小数
    """
    parasf = []
    for x in paras:
        if type(x) is float:
            parasf.append(round(x, 2))
        else:
            parasf.append(x)

    print(strf % tuple(parasf))


def celv(max_m, target_r, max_lost_r):
    """
        假设 正负的概率 是 50%
        double cask
        double cask => +100%

            or . .. .... ...... ? rate

        预设 first time 计算得出一个合理的 add_r

        1. first_b -> max_m * target_r
            max_m * target_r / first_b = lost_r / DOUBLE_CASK
            => first_b: DOUBLE_CASK * max_m * target_r / abs(lost_r)

        2. first_b -> max_m
            first_b * (DOUBLE_CASK ** Ta) = max_m / DOUBLE_CASK
            (DOUBLE_CASK ** Ta) = max_m / DOUBLE_CASK / first_b
            Ta = math.log(max_m / DOUBLE_CASK / first_b, DOUBLE_CASK)

        3. lost_r -> max_lost_r

            (1 - lost_r) ** Ta = (1 - max_lost_r)

            Ta = math.log((1 - max_lost_r), (1 - lost_r))

            32 = 2 ** 5
            math.log(32, 2) = 5


        max_m 基础 base
        target_r 目标 rate
        max_lost_r 损失 rate
    """

    DOUBLE_CASK = 2

    minr, minc = 0, 99
    ma, mb = 0, 0
    first_b = 0
    for i in range(1, 9999):

        r = -0.0001 * i
        b = DOUBLE_CASK * max_m * target_r / abs(r)

        # base > max
        if b > max_m:
            continue

        # 从 b 开始，直到用完的次数
        ta = math.log(max_m / DOUBLE_CASK / b, DOUBLE_CASK)

        # 从 r 开始 损失达到 max_lost_r 的次数 => 递减
        tb = math.log((1 - abs(max_lost_r)), (1 - abs(r)))

        # 找最接近的
        c = abs(ta - tb)
        if c < minc:
            first_b = b
            minc = c
            minr = r
            ma, mb = ta, tb

    add_r = minr
    printf("min c: %s, ta: %s, tb: %s, min r: %s", (minc, ma, mb, minr))
    printf("Max m is: %s + %s%% => %s, makeup rate: %s%%, max lost rate: %s%% \n", (
        max_m, target_r * 100, max_m * (1 + target_r), add_r * 100, max_lost_r * 100
    ))

    printf("Start base: %s + %s => %s, start rate: %s%%, target rate: %s%%", (
        first_b,
        max_m * target_r,
        first_b + max_m * target_r,
        ((max_m * target_r + first_b) / first_b - 1) * 100,
        (1 - (max_m * target_r + first_b) / first_b) * 100,
    ))

    for i in range(1, int((ma + mb) / 2) + 1):

        add_m = first_b * (2 ** (i - 1))
        lost_b = add_m * add_r
        lost_br = (1 - abs(add_r)) ** i - 1
        lost_rzz = lost_b / (add_m * 2)

        printf(
            "Add Time %s => "
            "add_m: %s, "
            "Total m: %s, "
            "lost_br: %s%%, "
            "lost_r: %s%%, "
            "lost_b: %s ", (
                i,
                add_m,
                add_m * 2,
                lost_br * 100,
                lost_rzz * 100,
                lost_b,
            )
        )


def main():
    """
        初始阶段：  目标值 == 回归值 基准
                    10000 * 1.02 == 10200
        目标
    """
    now_point = 3400
    worest_point = 2000
    target_point = 3600

    target_r = 0.02

    max_m = 10000 * 20
    max_lost_r = (worest_point - now_point) / now_point

    # max_lost_r = -0.10

    print("max in m is: %s, target_m: %s, worest lost rate from %s->%s is: %s%%" % (max_m, max_m * (1 + target_r), now_point, worest_point, round(max_lost_r * 100, 2)))

    celv(max_m=max_m, target_r=target_r, max_lost_r=max_lost_r)


def kelly(p, q, rW, rL):
    """
        https://zh.m.wikipedia.org/zh-hk/%E5%87%B1%E5%88%A9%E5%85%AC%E5%BC%8F
        凯利公式
        Args:
            p (float): 获胜概率
            q (float): 失败概率
            rW (float): 净利润率
            rL (float): 净亏损率
        Returns:
            float: 最大化利润的投资本金占比(%)

            kelly(0.6, 0.4, 1, 1) -> 0.02
    """
    return (p * rW - q * rL) / rW * rL


if __name__ == "__main__":
    main()
