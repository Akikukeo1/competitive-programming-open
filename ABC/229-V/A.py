a = str(input())
b = str(input())

dot = "."
sharp = "#"

if a[0] == dot and a[1] == sharp and b[0] == sharp and b[1] == dot:
    print("No")
elif a[0] == sharp and a[1] == dot and b[0] == dot and b[1] == sharp:
    print("No")
else:
    print("Yes")
