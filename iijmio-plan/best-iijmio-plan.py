# code:utf-8
# best-iijmio-plan.py
# IIJMIOのギガプラン検討用のスクリプト
# 回線数とトータル容量を満たす組み合わせで、最安のものを総当たりで計算する

import itertools

# ギガプランの容量と料金の一覧(2024年3月現在)
PLANS = [
    [ 2, 850 ],
    [ 5, 990 ],
    [ 10, 1500 ],
    [ 15, 1800 ],
    [ 20, 2000 ],
    [ 30, 2700 ],
    [ 40, 3300 ],
    [ 50, 3900 ],
]

# 容量の合計を得る
def comptuteCapacity(candidate):
    n = 0
    for item in candidate:
        n += item[0]
    return n

# 価格の合計を得る
def computePrice(candidate):
    price = 0
    for item in candidate:
        price += item[1]
    return price

# 条件を満たす最安の組み合わせを計算する
def computeBestPlan(capa_threshold, num_persons):

    # 選択結果
    best = None
    best_price = 0
    
    # 総当たりの組み合わせをみる
    all_candidates = itertools.combinations_with_replacement(PLANS, num_persons)
    for candidate in all_candidates:
        # 容量を満たさないものを除外
        if comptuteCapacity(candidate) < capa_threshold:
            continue

        if best == None:
            best = candidate
            best_price = computePrice(candidate)
            continue

        # 合計額が高ければ除外
        p = computePrice(candidate)
        if best_price < p:
            continue

        # その時点の条件を満たす最安の組み合わせを更新
        best = candidate
        best_price = p

    return best

if __name__ == "__main__":

    # 人数(回線数)
    num_persons = 4
    # ほしいトータル容量(GB)
    capa_threshold = 32

    best = computeBestPlan(capa_threshold, num_persons)
    if best == None:
        # capa_thresholdの値が大きすぎる場合
        print("該当なし")
        quit()

    # 結果を出力
    for plan in best:
        print(f"{plan[0]}GB : {plan[1]}円")
    print(f"合計: {comptuteCapacity(best)}GB {computePrice(best)}円")

