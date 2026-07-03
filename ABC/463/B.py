n, x = input().split()

seat_id = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
    "E": 4,
}

target = seat_id[x]

for _ in range(int(n)):
    s = input()

    if s[target] == "o":
        print("Yes")
        exit()

print("No")
