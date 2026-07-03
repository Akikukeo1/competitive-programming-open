N = int(input())

li = ["1"]

for i in range(N):
    li.extend(["0", "1"])

li_str = "".join(li)

print(li_str)
