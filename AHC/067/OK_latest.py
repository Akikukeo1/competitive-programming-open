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

    # 固定されたギミックの記録用
    fixed_switches = set()
    fixed_doors_h = set()
    fixed_doors_v = set()
    door_count = 0

    # 各マスの「隣接する通路（次数）」を計算して、行き止まりを特定する
    cell_degrees = {}
    for i, j in empty_cells:
        deg = 0
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                deg += 1
        cell_degrees[(i, j)] = deg

    def place_chain():
        nonlocal door_count
        if K == 0:
            return

        # 1. ゴール (N-1, N-1) の直前を最後のドアで塞ぐ
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

        # 2. 行き止まりマスを「右上」と「左下」に分離する
        tr_candidates = []  # 右上エリア (Top-Right)
        bl_candidates = []  # 左下エリア (Bottom-Left)

        for (i, j), deg in cell_degrees.items():
            if (i, j) == (0, 0) or (i, j) == (N - 1, N - 1):
                continue

            # マンハッタン距離や座標でエリアを分ける
            if i + j < N:  # 左上～左下寄り
                bl_candidates.append(((i, j), deg))
            else:  # 右上～右下寄り
                tr_candidates.append(((i, j), deg))

        # それぞれ「行き止まり度（degの小ささ）」でソート
        tr_candidates.sort(key=lambda x: x[1])
        bl_candidates.sort(key=lambda x: x[1])

        # 3. 偶数ステップと奇数ステップで、配置するエリアを「交互」にする
        for step in range(K - 1, -1, -1):
            # 奇数は右上、偶数は左下から選ぶ（逆でも可、交互にすることが最重要）
            pool = tr_candidates if (step % 2 == 1) else bl_candidates

            if not pool:
                # どちらかのエリアが枯渇したら、もう一方から補填
                pool = bl_candidates if (step % 2 == 1) else tr_candidates
            if not pool:
                break

            (si, sj), deg = pool.pop(0)
            switch[si][sj] = step
            fixed_switches.add((si, sj))

            # step 0 以外のスイッチは、その周囲の通路をドアで完全に封鎖
            if step > 0:
                door_val = 2 * (step - 1) + 1
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

    # 初期スコア計算
    best_T = calc_T(N, K, c, door_h, door_v, switch)

    # 3. 山登りループ (固定チェイン以外の余った枠で微調整)
    while time.time() - start_time < LIMIT:
        mode = random.randint(0, 1)

        if mode == 0:
            # ドアの追加・削除・変更
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 1)
            j = random.randint(0, N - 1)
            if d_type == 0 and i == N - 1:
                continue
            if d_type == 1 and j == N - 1:
                continue

            # 固定ギミックの扉は変更をスキップ
            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue

            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]

            # 削除、またはランダムな初期閉ドアの配置
            if old_g != -1 and random.random() < 0.4:
                new_g = -1
            else:
                if K == 0:
                    continue
                if old_g == -1 and door_count >= M:
                    continue
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
            # スイッチの追加・削除・変更
            if K == 0:
                continue
            i, j = random.choice(empty_cells)
            # 固定ギミックのスイッチは変更をスキップ
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

    # 結果の出力整形
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
