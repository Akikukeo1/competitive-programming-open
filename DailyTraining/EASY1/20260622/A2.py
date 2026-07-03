import sys

n = int(input())
p = list(map(int, input().split()))

if len(p) == 1:
    print("0")
    exit()

max_value = max(p[1:])

calc = max(0, max_value - p[0] + 1)

print(calc)
