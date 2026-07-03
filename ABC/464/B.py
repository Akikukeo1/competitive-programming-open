import sys

H, W = map(int, input().split())
C = []

for _ in range(H):
    C.append(input())

sys.stdout.write(str(C) + "\n")

for i in range(H-1):
    if C[0] not in '#':
        C.remove(C[0])

for j in range(H-1):
    print(C[j])

