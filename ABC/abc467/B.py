n=int(input())

x=int(0)

for i in range(n):
    a,b,c=map(str,input().split())
    a=int(a)
    b=int(b)
    if c=="keep":
        x+=b-a

print(x)