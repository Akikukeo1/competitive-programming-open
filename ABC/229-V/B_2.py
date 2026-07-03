import sys

a, b = map(int, input().split())

while a > 0 and b > 0:
    digit_a = a % 10
    digit_b = b % 10

    if digit_a + digit_b >= 10:
        print("Hard")
        sys.exit()

    a //= 10
    b //= 10

print("Easy")
