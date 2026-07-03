import sys

a, b = map(str, input().split())

# a = "229"
# b = "390"

sys.stderr.write(a + "\n")
sys.stderr.write(b + "\n")

for i in range(len(a)):
    sys.stderr.write(a[-i] + "\n")
    sys.stderr.write(b[-i] + "\n")

    if a[-i] + b[-i] <= "10":
        print("Hard")
        exit()

print("Easy")
