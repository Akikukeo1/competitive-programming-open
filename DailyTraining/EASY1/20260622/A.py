import sys

n = int(input())
p = list(map(int, input().split()))

max_value = max(p)

if p[0] == max_value + 1 or p[0] == max_value:
    print("0")
    exit()

# sys.stderr.write(str(max_value))

calc = max_value - p[0] + 1

print(calc)
