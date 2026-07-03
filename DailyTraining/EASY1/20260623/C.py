N, A, B = map(int, input().split())

for i in range(N):
    for _ in range(A):
        row = []
        for j in range(N):
            C = "." if (i + j) % 2 == 0 else "#"
            row.append(C * B)
        print("".join(row))
