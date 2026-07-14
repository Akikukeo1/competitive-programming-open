import sys

X, Y, L, R, A, B = map(int, input().split())

# DEBUG ONLY
# X, Y, L, R, A, B = 700, 300, 9, 17, 7, 21

sys.stderr.write(str(X) + "\n" + str(Y) + "\n")

total = []

total.append((L - A) * Y)
sys.stderr.write(str(list(total)) + "\n")
total.append((R - L) * X)
sys.stderr.write(str(list(total)) + "\n")
total.append((B - R) * Y)
sys.stderr.write(str(list(total)) + "\n")

print(sum(total))
