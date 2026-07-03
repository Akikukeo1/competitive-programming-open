S = input()

if S.count("E") < S.count("W"):
    print("West")
elif S.count("E") > S.count("W"):
    print("East")
