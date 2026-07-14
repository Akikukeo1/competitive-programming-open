X, Y, L, R, A, B = map(int, input().split())

X_time = max(min(R, B) - max(A, L), 0)
Y_time = (B - A) - X_time

print(X_time * X + Y_time * Y)
