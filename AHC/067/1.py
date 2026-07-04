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

    def place_chain_outer():
        nonlocal door_count
        if K == 0:
            return

        # ヘルパー関数: 拠点に近い空きマスを取得
        def get_cluster(anchor, num):
            if not anchor:
                return []
            que = deque([anchor])
            visited = {anchor}
            res = []
            while que and len(res) < num:
                curr = que.popleft()
                if c[curr[0]][curr[1]] == ".":
                    res.append(curr)
                for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    ni, nj = curr[0] + di, curr[1] + dj
                    if 0 <= ni < N and 0 <= nj < N and (ni, nj) not in visited:
                        visited.add((ni, nj))
                        que.append((ni, nj))
            return res

        # --------------------------------------------------
        # 1. 奇数・偶数エリアの拠点とクラスター（部屋）の確保
        # --------------------------------------------------
        tr_anchor = get_safe_endpoint(N, c, 0, N - 1)  # 右上奥
        bl_anchor = get_safe_endpoint(N, c, N - 1, 0)  # 左下奥
        if tr_anchor is None or bl_anchor is None:
            return

        num_odd = K // 2
        num_even = K - num_odd
        odd_cells = get_cluster(tr_anchor, num_odd)
        even_cells = get_cluster(bl_anchor, num_even)

        # --------------------------------------------------
        # 2. 限界まで外周を回る「大動脈ルート」を探索（保護マスの確定）
        # --------------------------------------------------
        protected_cells = set()

        # スイッチ部屋、スタート、ゴールは無条件で保護
        for cell in odd_cells + even_cells:
            protected_cells.add(cell)
        protected_cells.add((0, 0))
        protected_cells.add((N - 1, N - 1))

        # スタート -> 左下部屋の入り口 -> (左上経由) -> 右上部屋の入り口 -> ゴール
        # を結ぶ、極力中央を通らない（i+jが極端、または外周に近い）ルートを簡易BFSで開通させる
        def find_outer_road(start, end):
            que = deque([start])
            parent = {start: None}
            while que:
                curr = que.popleft()
                if curr == end:
                    break
                # 上下左右の移動（外周に近いものをソートして優先的に探索）
                neighbors = []
                for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    ni, nj = curr[0] + di, curr[1] + dj
                    if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                        # 外周（端）からの距離が近いほど優先度を高くするスコア
                        dist_to_edge = min(ni, N - 1 - ni, nj, N - 1 - nj)
                        neighbors.append((dist_to_edge, ni, nj))

                # 端に近い順にソートして探索キューへ
                neighbors.sort(key=lambda x: x[0])
                for _, ni, nj in neighbors:
                    if (ni, nj) not in parent:
                        parent[(ni, nj)] = curr
                        que.append((ni, nj))

            # パスを復元
            path = []
            curr = end
            while curr is not None:
                if curr in parent:
                    path.append(curr)
                    curr = parent[curr]
                else:
                    break
            return path

        # 各区間の外周ルートを計算して保護リストにマージ
        road1 = find_outer_road((0, 0), bl_anchor)  # スタート -> 左下
        road2 = find_outer_road(bl_anchor, tr_anchor)  # 左下 -> 右上
        road3 = find_outer_road(tr_anchor, (N - 1, N - 1))  # 右上 -> ゴール

        for cell in road1 + road2 + road3:
            protected_cells.add(cell)

        # --------------------------------------------------
        # 3. ルートの「内側」だけをフリー色の壁で埋め立てる
        # --------------------------------------------------
        dummy_door = 2 * K + 1
        # 35枚程度を上限に、内側の通行可能マスをドアで塞ぐ
        for i in range(N):
            for j in range(N):
                if door_count >= M or door_count >= 35:
                    break

                # 保護された大動脈ルートに乗っておらず、かつ通路である場所
                if (i, j) not in protected_cells and c[i][j] == ".":
                    # 隣接関係を見て壁（ドア）を設置
                    if i + 1 < N and (i + 1, j) not in protected_cells and c[i + 1][j] == "." and door_h[i][j] == -1:
                        door_h[i][j] = dummy_door
                        fixed_doors_h.add((i, j))
                        door_count += 1
                    elif j + 1 < N and (i, j + 1) not in protected_cells and c[i][j + 1] == "." and door_v[i][j] == -1:
                        door_v[i][j] = dummy_door
                        fixed_doors_v.add((i, j))
                        door_count += 1

        # --------------------------------------------------
        # 4. ゴール直前の絶対封鎖
        # --------------------------------------------------
        last_step = K - 1
        g_door = 2 * last_step + 1
        if N >= 2:
            if c[N - 2][N - 1] == "." and (N - 2, N - 1) not in fixed_doors_h:
                door_h[N - 2][N - 1] = g_door
                fixed_doors_h.add((N - 2, N - 1))
                door_count += 1
            elif c[N - 1][N - 2] == "." and (N - 1, N - 2) not in fixed_doors_v:
                door_v[N - 1][N - 2] = g_door
                fixed_doors_v.add((N - 1, N - 2))
                door_count += 1

        # --------------------------------------------------
        # 5. スイッチと連動ドアの配置（Step 0 はフリー）
        # --------------------------------------------------
        for step in range(K):
            if step % 2 == 0:
                if not even_cells:
                    continue
                si, sj = even_cells.pop(0)
            else:
                if not odd_cells:
                    continue
                si, sj = odd_cells.pop(0)

            switch[si][sj] = step
            fixed_switches.add((si, sj))

            # step 0 はフリー（障害物なし）。step > 0 のみ、前のスイッチに対応するドアを逆サイドの入り口に設置
            if step > 0 and door_count < M:
                door_type = 2 * (step - 1) + 1
                # 偶数ステップなら右上（奇数）の入り口を塞ぐ、奇数ステップなら左下（偶数）の入り口を塞ぐ
                target_anchor = tr_anchor if (step % 2 == 0) else bl_anchor

                # ターゲット拠点の隣接マスにロックドアを設置
                for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    ni, nj = target_anchor[0] + di, target_anchor[1] + dj
                    if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                        if di == 1 and (target_anchor[0], target_anchor[1]) not in fixed_doors_h:
                            door_h[target_anchor[0]][target_anchor[1]] = door_type
                            fixed_doors_h.add((target_anchor[0], target_anchor[1]))
                            door_count += 1
                            break
                        elif di == -1 and (ni, nj) not in fixed_doors_h:
                            door_h[ni][nj] = door_type
                            fixed_doors_h.add((ni, nj))
                            door_count += 1
                            break
                        elif dj == 1 and (target_anchor[0], target_anchor[1]) not in fixed_doors_v:
                            door_v[target_anchor[0]][target_anchor[1]] = door_type
                            fixed_doors_v.add((target_anchor[0], target_anchor[1]))
                            door_count += 1
                            break
                        elif dj == -1 and (ni, nj) not in fixed_doors_v:
                            door_v[ni][nj] = door_type
                            fixed_doors_v.add((ni, nj))
                            door_count += 1
                            break

    place_chain_outer()

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
