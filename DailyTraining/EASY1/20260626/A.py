cards = list(map(int, input().split()))
cards.sort()

card1 = (cards[0] == cards[1] == cards[2]) and (cards[2] != cards[3])
card2 = (cards[0] != cards[1]) and (cards[1] == cards[2] == cards[3])
card3 = (cards[0] == cards[1]) and (cards[1] != cards[2]) and (cards[2] == cards[3])

if card1 or card2 or card3:
    print("Yes")
else:
    print("No")
