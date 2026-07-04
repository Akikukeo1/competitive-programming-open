import sys
import time
import random
from collections import deque


def calc_T(N, K, c, door_h, door_v, switch):
    def is_open(g, mask):
        if g == -1:
            return True
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


def get_safe_endpoint(N, c, target_i, target_j):
    """指定した座標に近い、障害物ではないマスを探す安全関数"""
    best_pos = None
    min_d = 999
    for i in range(N):
        for j in range(N):
            if c[i][j] == ".":
                d = abs(i - target_i) + abs(j - target_j)
                if d < min_d:
                    min_d = d
                    best_pos = (i, j)
    return best_pos


def solve():
    start_time = time.time()
    LIMIT = 1.7

    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N, M, K = int(input_data[0]), int(input_data[1]), int(input_data[2])
    c = input_data[3 : 3 + N]

    empty_cells = [(i, j) for i in range(N) for j in range(N) if c[i][j] == "."]

    # 各空きマスの「隣接する通路の数」を計算
    cell_degrees = {}
    for i, j in empty_cells:
        deg = 0
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                deg += 1
        cell_degrees[(i, j)] = deg

    door_h = [[-1] * N for _ in range(N)]
    door_v = [[-1] * N for _ in range(N)]
    switch = [[-1] * N for _ in range(N)]

    # 1. 通常の最短経路を計算
    dist_init = [[-1] * N for _ in range(N)]
    prev_init = [[None] * N for _ in range(N)]
    que = deque([(0, 0)])
    dist_init[0][0] = 0
    found = False
    while que:
        i, j = que.popleft()
        if (i, j) == (N - 1, N - 1):
            found = True
            break
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == "." and dist_init[ni][nj] == -1:
                dist_init[ni][nj] = dist_init[i][j] + 1
                prev_init[ni][nj] = (i, j)
                que.append((ni, nj))
    path = []
    if found:
        curr = (N - 1, N - 1)
        while curr is not None:
            path.append(curr)
            curr = prev_init[curr[0]][curr[1]]
        path.reverse()

    # 固定されたギミックのカウント用
    fixed_switches = set()
    fixed_doors_h = set()
    fixed_doors_v = set()
    door_count = 0

    def place_chain():
        nonlocal door_count
        if K == 0:
            return

        # 1. ゴール直前の封鎖（既存の処理）
        goal_door_placed = False
        if N >= 2:
            if c[N - 2][N - 1] == ".":
                door_h[N - 2][N - 1] = 2 * (K - 1) + 1
                fixed_doors_h.add((N - 2, N - 1))
                door_count += 1
                goal_door_placed = True
            elif c[N - 1][N - 2] == "." and not goal_door_placed:
                door_v[N - 1][N - 2] = 2 * (K - 1) + 1
                fixed_doors_v.add((N - 1, N - 2))
                door_count += 1
                goal_door_placed = True

        # 2. スイッチ候補地を通路の少なさ（行き止まり優先）でソート
        # スタート(0,0)とゴール(N-1,N-1)は除外
        candidates = [(cell, cell_degrees[cell]) for cell in empty_cells if cell != (0, 0) and cell != (N - 1, N - 1)]
        # deg が小さい（行き止まり）順にソート
        candidates.sort(key=lambda x: x[1])

        # 依存チェーンの配置
        for step in range(K - 1, -1, -1):
            if not candidates:
                break

            # 最も行き止まりに近いマスをポップ
            (si, sj), deg = candidates.pop(0)
            switch[si][sj] = step
            fixed_switches.add((si, sj))

            # step 0 以外は、このスイッチの手前を「前のステップのドア」で塞ぐ
            if step > 0:
                door_val = 2 * (step - 1) + 1
                # このスイッチに隣接するすべての通路にドアを設置して完全に閉じ込める
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = si + di, sj + dj
                    if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                        if di == 1 and (si, sj) not in fixed_doors_h:
                            door_h[si][sj] = door_val
                            fixed_doors_h.add((si, sj))
                            door_count += 1
                        elif di == -1 and (ni, nj) not in fixed_doors_h:
                            door_h[ni][nj] = door_val
                            fixed_doors_h.add((ni, nj))
                            door_count += 1
                        elif dj == 1 and (si, sj) not in fixed_doors_v:
                            door_v[si][sj] = door_val
                            fixed_doors_v.add((si, sj))
                            door_count += 1
                        elif dj == -1 and (ni, nj) not in fixed_doors_v:
                            door_v[ni][nj] = door_val
                            fixed_doors_v.add((ni, nj))
                            door_count += 1

    place_chain()

    best_T = calc_T(N, K, c, door_h, door_v, switch)

    # 3. 山登りループ (固定ギミック以外の場所を最適化)
    while time.time() - start_time < LIMIT:
        mode = random.randint(0, 1)

        if mode == 0:
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 1)
            j = random.randint(0, N - 1)
            if d_type == 0 and i == N - 1:
                continue
            if d_type == 1 and j == N - 1:
                continue

            # 固定ギミックの扉は変更しない
            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue

            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]

            if old_g != -1 and random.random() < 0.4:
                new_g = -1
            else:
                if K == 0:
                    continue
                if old_g == -1 and door_count >= M:
                    continue
                # 残りの奇数型(初期閉)をランダムに配置
                new_g = random.choice([2 * k + 1 for k in range(K)])

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

        else:
            if K == 0:
                continue
            i, j = random.choice(empty_cells)
            # 固定ギミックのスイッチは変更しない
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

    # 出力
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
