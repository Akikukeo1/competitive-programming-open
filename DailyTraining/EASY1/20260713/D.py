import sys


s=input()

if len(s)%2!=0:
    print("No")
    print("Sは奇数",file=sys.stderr)
    sys.exit()

for i in range(0,len(s),2):
    if s[i]==s[i+1]:
        pass
    else:
        print("No")
        print("ペアではない",file=sys.stderr)
        sys.exit()

for char in s:
    if s.count(char)!=2:
        print("No")
        print("文字数が2ではない",file=sys.stderr)
        sys.exit()

print("Yes")