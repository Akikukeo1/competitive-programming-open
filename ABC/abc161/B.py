import sys

n, m = map(int, input().split())

a = list(map(int, input().split()))

print(f"{n, m, a=}", file=sys.stderr)

total_vote = sum(a)

print(f"{total_vote=}", file=sys.stderr)

counter = 0

for i in range(len(a)):
    if a[i] * 4 * m >= total_vote:
        counter += 1

if counter >= total_vote:
    print("Yes")
else:
    print("No")
