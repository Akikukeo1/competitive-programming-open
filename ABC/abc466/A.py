N=int(input())
X=list(map(int,input().split()))

for i in range(N):
    if X[i]>=0:
        print("No")
        exit()

print("Yes")