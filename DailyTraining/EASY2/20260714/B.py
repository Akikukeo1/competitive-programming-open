a,b,c,d,e,f,x=map(int,input().split())

takahashi_T=(x//(a+c))*a+min(x%(a+c),a)
aoki_T     =(x//(d+f))*d+min(x%(d+f),d)

if takahashi_T*b > aoki_T*e:
    print("Takahashi")
elif takahashi_T*b < aoki_T*e:
    print("Aoki")
else:
    print("Draw")