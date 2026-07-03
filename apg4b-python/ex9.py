N = int(input())
A = int(input())

for i in range(N):
    op, B = input().split()
    B = int(B)

    if op == "+":
        A += B
        print(i + 1, A)
    elif op == "-":
        A -= B
        print(i + 1, A)
    elif op == "*":
        A *= B
        print(i + 1, A)
    elif op == "/" and B != 0:
        A //= B
        print(i + 1, A)
    else:
        print("error")
        break
