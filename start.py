import time
import random
import math


class State:
    def __init__(self):
        self.a = []
        self.score = 0


def calc_score(s: State):
    return s.score  # or full calc


def make_move(s: State):
    n = len(s.a)
    i = random.randint(0, n - 1)
    j = random.randint(0, n - 1)
    return i, j


def apply(s: State, m):
    i, j = m
    s.a[i], s.a[j] = s.a[j], s.a[i]


def hillclimb(s: State, TL=0.3):
    start = time.time()

    while time.time() - start < TL:
        m = make_move(s)
        old = s.score

        apply(s, m)
        new = calc_score(s)

        if new >= old:
            s.score = new
        else:
            apply(s, m)  # rollback


def sa(s: State, TL=1.9):
    start = time.time()

    cur = s
    best = s

    startT = 100
    endT = 0.1

    while True:
        t = time.time() - start
        if t > TL:
            break

        temp = startT + (endT - startT) * (t / TL)

        m = make_move(cur)
        old = cur.score

        apply(cur, m)
        new = calc_score(cur)

        diff = new - old

        if diff > 0 or math.exp(diff / temp) > random.random():
            cur.score = new
            if cur.score > best.score:
                best = cur
        else:
            apply(cur, m)

    return best


def main():
    random.seed(42)  # 再現性のための固定シード


if __name__ == "__main__":
    main()
