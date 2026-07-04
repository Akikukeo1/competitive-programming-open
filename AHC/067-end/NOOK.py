import sys
import time
import random
from collections import deque


def calc_T(N, K, c, door_h, door_v, switch):
    def is_open(g, mask):
        if g == -1:
            return True
        # 末尾が1ならONで開く、0ならOFFで開く
        return ((mask >> (g // 2)) & 1) == (g & 1)

    dist = [[[-1] * N for _ in range(N)] for _ in range(1 << K)]
    dist[0][0][0] = 0
    que = deque([(0, 0, 0)])

    while que:
        mask, i, j = que.popleft()
        d = dist[mask][i][j]

        if (i, j) == (N - 1, N - 1):
            return d

        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if not (0 <= ni < N and 0 <= nj < N) or c[ni][nj] == "#":
                continue

            if di == 1:
                g = door_h[i][j]
            elif di == -1:
                g = door_h[ni][nj]
            elif dj == 1:
                g = door_v[i][j]
            else:
                g = door_v[ni][nj]

            if not is_open(g, mask):
                continue

            if dist[mask][ni][nj] == -1:
                dist[mask][ni][nj] = d + 1
                que.append((mask, ni, nj))

        s = switch[i][j]
        if s != -1:
            nmask = mask ^ (1 << s)
            if dist[nmask][i][j] == -1:
                dist[nmask][i][j] = d + 1
                que.append((nmask, i, j))
    return 0


def solve():
    start_time = time.time()
    LIMIT = 1.7

    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N, M, K = int(input_data[0]), int(input_data[1]), int(input_data[2])
    c = input_data[3 : 3 + N]

    empty_cells = [(i, j) for i in range(N) for j in range(N) if c[i][j] == "."]

    door_h = [[-1] * N for _ in range(N)]
    door_v = [[-1] * N for _ in range(N)]
    switch = [[-1] * N for _ in range(N)]

    fixed_switches = set()
    fixed_doors_h = set()
    fixed_doors_v = set()
    door_count = 0

    def set_door(i, j, ni, nj, val):
        nonlocal door_count
        if door_count >= M:
            return False
        if i == ni:  # 左右の移動 -> 垂直ドア
            col = min(j, nj)
            if door_v[i][col] == -1:
                door_v[i][col] = val
                fixed_doors_v.add((i, col))
                door_count += 1
                return True
        else:  # 上下の移動 -> 水平ドア
            row = min(i, ni)
            if door_h[row][j] == -1:
                door_h[row][j] = val
                fixed_doors_h.add((row, j))
                door_count += 1
                return True
        return False

    def place_baguenaudier():
        nonlocal door_count
        if K == 0:
            return

        # 1. 1本道の袋小路（長さ3以上）を抽出する
        baguenaudier_spots = []
        for i, j in empty_cells:
            if (i, j) == (0, 0) or (i, j) == (N - 1, N - 1):
                continue

            path = [(i, j)]
            curr_i, curr_j = i, j
            visited = {(i, j)}

            while True:
                neighbors = []
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = curr_i + di, curr_j + dj
                    if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == "." and (ni, nj) not in visited:
                        # 分岐のない純粋な通路かチェック
                        n_deg = sum(
                            1
                            for ddi, ddj in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                            if 0 <= ni + ddi < N and 0 <= nj + ddj < N and c[ni + ddi][nj + ddj] == "."
                        )
                        if n_deg <= 2:
                            neighbors.append((ni, nj))

                if len(neighbors) == 1:
                    next_cell = neighbors[0]
                    path.append(next_cell)
                    visited.add(next_cell)
                    curr_i, curr_j = next_cell
                else:
                    break

            if len(path) >= 2:
                baguenaudier_spots.append(path)

        # マップの右下・外周に近い方を後半の重いビット（K-1, K-2...）にする
        baguenaudier_spots.sort(key=lambda p: p[0][0] + p[0][1], reverse=True)

        # 2. 各スイッチと直列ロックドアのハメコミ
        for k in range(min(K, len(baguenaudier_spots))):
            path = baguenaudier_spots[k]
            si, sj = path[0]  # 一番奥

            switch[si][sj] = k
            fixed_switches.add((si, sj))

            # [検問1] 1歩手前に、k-1 が ON で開くドア (2*(k-1) + 1)
            if k > 0 and len(path) >= 2:
                door_on = 2 * (k - 1) + 1
                set_door(si, sj, path[1][0], path[1][1], door_on)

            # [検問2] 2歩手前に、k-2 が OFF で開くドア (2*(k-2))
            if k >= 2 and len(path) >= 3:
                door_off = 2 * (k - 2)
                set_door(path[1][0], path[1][1], path[2][0], path[2][1], door_off)

        # 3. ゴール直前を「すべての連鎖が解けた状態（最後のONドア）」で塞ぐ
        if door_count < M:
            final_door = 2 * (K - 1) + 1
            if N >= 2:
                if c[N - 2][N - 1] == "." and (N - 2, N - 1) not in fixed_doors_h:
                    door_h[N - 2][N - 1] = final_door
                    fixed_doors_h.add((N - 2, N - 1))
                    door_count += 1
                elif c[N - 1][N - 2] == "." and (N - 1, N - 2) not in fixed_doors_v:
                    door_v[N - 1][N - 2] = final_door
                    fixed_doors_v.add((N - 1, N - 2))
                    door_count += 1

    # 初期構築の実行
    place_baguenaudier()
    best_T = calc_T(N, K, c, door_h, door_v, switch)

    # 3. 山登り法（残ったリソースで、さらに経路をねじ曲げる調整）
    while time.time() - start_time < LIMIT:
        mode = random.randint(0, 1)

        if mode == 0:  # ドアの追加・削除
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 1)
            j = random.randint(0, N - 1)
            if d_type == 0 and i == N - 1:
                continue
            if d_type == 1 and j == N - 1:
                continue

            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue

            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]

            if old_g != -1 and random.random() < 0.4:
                new_g = -1
            else:
                if K == 0 or door_count >= M:
                    continue
                # 偶数（OFFで開く）と奇数（ONで開く）の両方を候補にする
                new_g = random.randint(0, 2 * K - 1)

            if d_type == 0:
                door_h[i][j] = new_g
            else:
                door_v[i][j] = new_g

            new_T = calc_T(N, K, c, door_h, door_v, switch)
            if new_T > best_T:
                best_T = new_T
                if old_g == -1 and new_g != -1:
                    door_count += 1
                elif old_g != -1 and new_g == -1:
                    door_count -= 1
            else:
                if d_type == 0:
                    door_h[i][j] = old_g
                else:
                    door_v[i][j] = old_g

        else:  # スイッチの追加・削除・変更
            if K == 0:
                continue
            i, j = random.choice(empty_cells)
            if (i, j) in fixed_switches:
                continue

            old_s = switch[i][j]
            if old_s != -1 and random.random() < 0.3:
                new_s = -1
            else:
                new_s = random.randint(0, K - 1)

            switch[i][j] = new_s

            new_T = calc_T(N, K, c, door_h, door_v, switch)
            if new_T > best_T:
                best_T = new_T
            else:
                switch[i][j] = old_s

    # 出力整形
    out_doors = []
    for i in range(N):
        for j in range(N):
            if door_h[i][j] != -1:
                out_doors.append((0, i, j, door_h[i][j]))
            if door_v[i][j] != -1:
                out_doors.append((1, i, j, door_v[i][j]))
    out_switches = []
    for i in range(N):
        for j in range(N):
            if switch[i][j] != -1:
                out_switches.append((i, j, switch[i][j]))

    print(len(out_doors))
    for d, i, j, g in out_doors:
        print(f"{d} {i} {j} {g}")
    print(len(out_switches))
    for p, q, s in out_switches:
        print(f"{p} {q} {s}")


if __name__ == "__main__":
    solve()
