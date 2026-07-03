N = int(input())

A = list(map(int, input().split()))
B = list(map(int, input().split()))

"""
3
3 1 2
2 3 1
"""

# print(A)
# print(B)


# if A[0] == 1:
#     if B[-1] == 1:
#         print("Yes")
#     if B[-1] == 2:
#         print("Yes")
#     if B[-1] == 3:
#         print("Yes")
# elif A[0] == 2:
#     if B[-2] == 1:
#         print("Yes")
#     if B[-2] == 2:
#         print("Yes")
#     if B[-2] == 3:
#         print("Yes")
# elif A[0] == 3:
#     if B[-3] == 1:
#         print("Yes")
#     if B[-3] == 2:
#         print("Yes")
#     if B[-3] == 3:
#         print("Yes")
# elif A[0] == 4:
#     if B[-4] == 1:
#         print("Yes")
#     if B[-4] == 2:
#         print("Yes")
#     if B[-4] == 3:
#         print("Yes")
# else:
#     print("No")

# # これをfor文で書くと
# for i in range(N):
#     if A[0] == i + 1:
#         if B[-i - 1] == 1:
#             print("Yes")
#             break
#         if B[-i - 1] == 2:
#             print("Yes")
#             break
#         if B[-i - 1] == 3:
#             print("Yes")
#             break
#     else:
#         print("No")
#         break

for i in range(N):
    if B[A[i] - 1] != i + 1:
        print("No")
        break
else:
    print("Yes")
