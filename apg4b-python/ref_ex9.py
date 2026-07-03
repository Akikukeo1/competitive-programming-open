N = int(input())
A = int(input())

for i in range(N):
    op, X = input().split()
    X = int(X)

    if op == "+":
        A += X
    elif op == "-":
        A -= X
    elif op == "*":
        A *= X
    elif op == "/" and X != 0:
        A //= X
    else:
        print("error")
        break

    print(i + 1, A)
