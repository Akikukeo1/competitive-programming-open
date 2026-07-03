x, y = map(int, input().split())

if x * 9 == y * 16:
    print("Yes")
else:
    print("No")


# 初期解、遅い
# import math
# common = math.gcd(x, y)
# aspect_w = x // common
# aspect_h = y // common

# if aspect_w == 16 and aspect_h == 9:
#     print("Yes")
# else:
#     print("No")
