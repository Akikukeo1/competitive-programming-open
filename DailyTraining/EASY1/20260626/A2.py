from collections import Counter

cards = list(map(int, input().split()))
count = Counter(cards)

count_list = sorted(count.values(), reverse=True)

if count_list == [3, 1] or count_list == [2, 2]:
    print("Yes")
else:
    print("No")
