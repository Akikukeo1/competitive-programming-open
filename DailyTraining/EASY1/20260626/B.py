S, T, X = map(int, input().split())

if S < T:
    if S < X < T:
        print("Yes")
    else:
        print("No")
else:
    if X >= S or X < T:
        print("Yes")
    else:
        print("No")
