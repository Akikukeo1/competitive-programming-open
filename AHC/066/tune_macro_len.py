import sys
import collections
import time
import random
import math

DR = (-1, 0, 1, 0)
DC = (0, 1, 0, -1)
DIR_NAMES = ["U", "R", "D", "L"]
INF = 10**9


def get_best_for_macro_len(n, m, v_walls, h_walls, balls, baskets, macro_len, time_limit):
    start_time = time.time()

    unique_positions = [(0, 0)]
    pos_to_idx = {(0, 0): 0}
    for p in balls + baskets:
        if p not in pos_to_idx:
            pos_to_idx[p] = len(unique_positions)
            unique_positions.append(p)
    num_unique = len(unique_positions)

    def can_move_forward(r, c, d):
        if d == 0:
            return r > 0 and h_walls[r - 1][c] == "0"
        if d == 1:
            return c < n - 1 and v_walls[r][c] == "0"
        if d == 2:
            return r < n - 1 and h_walls[r][c] == "0"
        if d == 3:
            return c > 0 and v_walls[r][c - 1] == "0"
        return False

    adj_dist = [[[[INF] * 4 for _ in range(num_unique)] for _ in range(4)] for _ in range(num_unique)]
    for s_idx in range(num_unique):
        sr, sc = unique_positions[s_idx]
        for sd in range(4):
            dists = [[[INF] * 4 for _ in range(n)] for _ in range(n)]
            queue = collections.deque([(sr, sc, sd)])
            dists[sr][sc][sd] = 0
            while queue:
                r, c, d = queue.popleft()
                curr_d = dists[r][c][d]
                if can_move_forward(r, c, d):
                    nr, nc = r + DR[d], c + DC[d]
                    if dists[nr][nc][d] > curr_d + 1:
                        dists[nr][nc][d] = curr_d + 1
                        queue.append((nr, nc, d))
                for nd in [(d + 1) % 4, (d - 1) % 4]:
                    if dists[r][c][nd] > curr_d + 1:
                        dists[r][c][nd] = curr_d + 1
                        queue.append((r, c, nd))

                # Macro L steps
                curr_r, curr_c = r, c
                possible = True
                for _ in range(macro_len):
                    if can_move_forward(curr_r, curr_c, d):
                        curr_r += DR[d]
                        curr_c += DC[d]
                    else:
                        possible = False
                        break
                if possible:
                    if dists[curr_r][curr_c][d] > curr_d + 1:
                        dists[curr_r][curr_c][d] = curr_d + 1
                        queue.append((curr_r, curr_c, d))
            for d_idx in range(num_unique):
                dr_pos, dc_pos = unique_positions[d_idx]
                for dd in range(4):
                    adj_dist[s_idx][sd][d_idx][dd] = dists[dr_pos][dc_pos][dd]

    ball_indices = [pos_to_idx[p] for p in balls]
    basket_indices = [pos_to_idx[p] for p in baskets]
    state = list(range(m))
    random.shuffle(state)

    def get_score(current_state):
        dp0, dp1, dp2, dp3 = INF, 0, INF, INF
        curr_pos_idx = 0
        for idx in current_state:
            b_idx, bk_idx = ball_indices[idx], basket_indices[idx]
            # To Ball
            a = adj_dist[curr_pos_idx]
            n0, n1, n2, n3 = INF, INF, INF, INF
            for d, dp_val in enumerate([dp0, dp1, dp2, dp3]):
                if dp_val < INF:
                    row = a[d][b_idx]
                    n0 = min(n0, dp_val + row[0])
                    n1 = min(n1, dp_val + row[1])
                    n2 = min(n2, dp_val + row[2])
                    n3 = min(n3, dp_val + row[3])
            dp0, dp1, dp2, dp3 = n0 + 1, n1 + 1, n2 + 1, n3 + 1
            curr_pos_idx = b_idx
            # To Basket
            a = adj_dist[curr_pos_idx]
            n0, n1, n2, n3 = INF, INF, INF, INF
            for d, dp_val in enumerate([dp0, dp1, dp2, dp3]):
                if dp_val < INF:
                    row = a[d][bk_idx]
                    n0 = min(n0, dp_val + row[0])
                    n1 = min(n1, dp_val + row[1])
                    n2 = min(n2, dp_val + row[2])
                    n3 = min(n3, dp_val + row[3])
            dp0, dp1, dp2, dp3 = n0 + 1, n1 + 1, n2 + 1, n3 + 1
            curr_pos_idx = bk_idx
        return min(dp0, dp1, dp2, dp3)

    current_score = get_score(state)
    best_score = current_score
    best_state = state[:]

    t_start, t_end = 10.0, 0.1
    while time.time() - start_time < time_limit:
        t = t_start * ((t_end / t_start) ** ((time.time() - start_time) / time_limit))
        i, j = random.sample(range(m), 2)
        state[i], state[j] = state[j], state[i]
        new_score = get_score(state)
        if new_score < current_score or random.random() < math.exp((current_score - new_score) / t):
            current_score = new_score
            if current_score < best_score:
                best_score = current_score
                best_state = state[:]
        else:
            state[i], state[j] = state[j], state[i]

    return best_score + macro_len + 2


def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    it = iter(input_data)
    n, m = int(next(it)), int(next(it))
    next(it)
    v_walls = [next(it) for _ in range(n)]
    h_walls = [next(it) for _ in range(n - 1)]
    balls, baskets = [], []
    for _ in range(m):
        r1, c1, r2, c2 = int(next(it)), int(next(it)), int(next(it)), int(next(it))
        balls.append((r1, c1))
        baskets.append((r2, c2))

    for L in range(2, 11):
        score = get_best_for_macro_len(n, m, v_walls, h_walls, balls, baskets, L, 2.0)
        print(f"L={L}, Best Score: {score}")


main()
