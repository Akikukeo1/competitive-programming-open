N = int(input())
A = list(map(int, input().split()))

out = 0

while True:
    all_even = True
    for x in A:
        if x % 2 != 0:
            all_even = False
            break

    if not all_even:
        break

    for i in range(N):
        A[i] = A[i] // 2

    out += 1

print(out)
