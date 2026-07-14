n,l,r=map(int,input().split())
s=input()

lx=l-1
rx=r-1

if s[lx:rx+1].count("o")==rx-lx+1:
    print("Yes")
else:
    print("No")