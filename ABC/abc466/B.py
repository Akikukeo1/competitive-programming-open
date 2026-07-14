import sys


N,M=map(int,input().split())

ans=[-1]*(M+1)

print(f"{ans=}", file=sys.stderr)

for i in range(N):
    C,S=map(int,input().split())
    ans[C] = max(ans[C],S)
    print(f"{ans=}", file=sys.stderr)

for i in range(1,M+1):
    print(ans[i],end=" ")