a=[]

while True:
    try:
        line=input()
        a.append(line)
    except EOFError:
        break

for x in reversed(a):
    print(x)