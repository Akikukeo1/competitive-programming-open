import sys

N, K = map(int, input().split())
print(f"{N=}", file=sys.stderr)

N %= K
print(f"{N=}", file=sys.stderr)

if N > K - N:
    print(K - N)
else:
    print(N)
