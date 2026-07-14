import sys


n=int(input())
x=0

for i in range(1,n):
    # 初期化
    left=i
    right=n+1

    while right-left>1:
        # 中央値の計算
        mid=(left+right)//2
        
        # インタラクティブジャッジに問い合わせ、代入する
        print(f"? {i} {mid}", flush=True)
        inter=input()

        # 探索する
        if inter=="Yes":
            left=mid
        else:
            right=mid

    x+=left-i
    print(f"経過個数.{x=}", file=sys.stderr)

print(f"! {x}", flush=True)