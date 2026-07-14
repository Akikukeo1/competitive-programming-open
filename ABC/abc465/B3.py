X, Y, L, R, A, B = map(int, input().split())

print(((max(min(R, B) - max(A, L), 0)) * X) + (((B - A) - (max(min(R, B) - max(A, L), 0))) * Y))
