import sys


n, d = map(int, input().split())
t = list(map(int, input().split()))

# print(f"{t=}",file=sys.stderr)

for i in range(n - 1):
    if t[i + 1] - t[i] <= d:
        print(t[i + 1])
        sys.exit()

print("-1")
