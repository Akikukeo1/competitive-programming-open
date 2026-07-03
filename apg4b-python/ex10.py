N = int(input())
A = list(map(int, input().split()))

total = 0

for i in range(N):
    total += A[i]

mean = total // N

for i in range(N):
    print(abs(A[i] - mean))  # abs()を使って、より綺麗に


"""
# 模範解答
N = int(input())

# スペース区切りの整数をリストとして受け取る
A = list(map(int, input().split()))

# 合計点
total = 0

# 合計点を計算
for i in range(N):
    # ①ここにプログラムを追記
    total += A[i]

# 平均点 (Nで割って切り捨てた値)
mean = total // N

# 平均点から何点離れているかを計算して出力
for i in range(N):
    # ②ここにプログラムを追記
    # 負の数を出力しないように注意
    if A[i] > mean:
        print(A[i] - mean)
    else:
        print(mean - A[i])
"""
