n=int(input())
a=list(map(int,input().split()))
ans=[]

for x in a:
    if x%2==0:
        ans.append(x)

for i in range(len(ans)):
    print(ans[i],end=" ")