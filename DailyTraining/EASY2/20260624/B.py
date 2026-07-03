h, w = map(int, input().split())

total = 0
for _ in range(h):
    total += input().count("#")

print(total)
