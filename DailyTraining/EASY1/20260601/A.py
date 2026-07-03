S = str(input())

output = int()

for i in range(1, 7):
    output = S * i

    if len(output) == 6:
        break


print(output)
