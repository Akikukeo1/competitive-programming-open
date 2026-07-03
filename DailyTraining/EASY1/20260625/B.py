s = str(input())

original = "abcdefghijklmnopqrstuvwxyz"

print(list(set(original) - set(s))[0])
