import sys
import collections
import time
import random
import math

# 定数
DR = (-1, 0, 1, 0)  # 上, 右, 下, 左
DC = (0, 1, 0, -1)
DIR_NAMES = ["U", "R", "D", "L"]
INF = 10**9


def solve():
    # 1. プログラム全体の開始時刻を記録
    start_time = time.time()
    # BFS の計測開始時刻を記録
    bfs_start_time = time.perf_counter()
    time_limit = 1.75  # ジャッジのブレを考慮したチキンレース

    random.seed(42)  # 再現性のための固定シード

    # -------------------------------------------------------------------------
    # 計測用
    # -------------------------------------------------------------------------
    score_calls = 0
    score_time = 0.0

    # 入力処理
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    it = iter(input_data)

    n = int(next(it))
    m = int(next(it))
    int(next(it))

    v_walls = [next(it) for _ in range(n)]  # 縦の壁 (i, j) と (i, j+1) の間
    h_walls = [next(it) for _ in range(n - 1)]  # 横の壁 (i, j) と (i+1, j) の間

    balls = []
    baskets = []
    for _ in range(m):
        r1, c1, r2, c2 = int(next(it)), int(next(it)), int(next(it)), int(next(it))
        balls.append((r1, c1))
        baskets.append((r2, c2))

    # 特徴的な座標のインデックス化
    unique_positions = [(0, 0)]
    pos_to_idx = {(0, 0): 0}
    for p in balls + baskets:
        if p not in pos_to_idx:
            pos_to_idx[p] = len(unique_positions)
            unique_positions.append(p)

    num_unique = len(unique_positions)

    # 壁判定のヘルパー関数
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

    # -------------------------------------------------------------------------
    # 1. 拡張BFSによる全点対最短経路・コスト計算（マクロ FFF をコスト1で組み込む）
    # -------------------------------------------------------------------------
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

                # 通常移動 F (コスト1)
                if can_move_forward(r, c, d):
                    nr, nc = r + DR[d], c + DC[d]
                    if dists[nr][nc][d] > curr_d + 1:
                        dists[nr][nc][d] = curr_d + 1
                        queue.append((nr, nc, d))

                # 通常旋回 R, L (コスト1)
                for nd in [(d + 1) % 4, (d - 1) % 4]:
                    if dists[r][c][nd] > curr_d + 1:
                        dists[r][c][nd] = curr_d + 1
                        queue.append((r, c, nd))

                # 【マクロ FFF 遷移】3歩前進できるなら、コスト1（マクロ呼び出し P の 1文字分）で遷移
                r1, c1 = r + DR[d], c + DC[d]
                if 0 <= r1 < n and 0 <= c1 < n and can_move_forward(r, c, d):
                    r2, c2 = r1 + DR[d], c1 + DC[d]
                    if 0 <= r2 < n and 0 <= c2 < n and can_move_forward(r1, c1, d):
                        r3, c3 = r2 + DR[d], c2 + DC[d]
                        if 0 <= r3 < n and 0 <= c3 < n and can_move_forward(r2, c2, d):
                            if dists[r3][c3][d] > curr_d + 1:
                                dists[r3][c3][d] = curr_d + 1
                                queue.append((r3, c3, d))

            # キャッシュに保存
            for d_idx in range(num_unique):
                dr_pos, dc_pos = unique_positions[d_idx]
                for dd in range(4):
                    adj_dist[s_idx][sd][d_idx][dd] = dists[dr_pos][dc_pos][dd]

    # BFS の計測終了時刻を記録
    bfs_end_time = time.perf_counter()

    # -------------------------------------------------------------------------
    # 2. 焼きなまし法 (SA) による順列最適化（バグのない高速DP）
    # -------------------------------------------------------------------------
    ball_indices = [pos_to_idx[p] for p in balls]
    basket_indices = [pos_to_idx[p] for p in baskets]

    state = list(range(m))
    random.shuffle(state)

    def get_score(current_state):
        nonlocal score_calls, score_time
        st = time.perf_counter()

        adj = adj_dist
        balls_idx = ball_indices
        baskets_idx = basket_indices
        inf = INF

        dp0 = inf
        dp1 = 0
        dp2 = inf
        dp3 = inf
        curr_pos_idx = 0

        for idx in current_state:
            b_idx = balls_idx[idx]
            bk_idx = baskets_idx[idx]

            # --- 1. 現在地 -> ボール ---
            adj_curr = adj[curr_pos_idx]
            a0 = adj_curr[0]
            a1 = adj_curr[1]
            a2 = adj_curr[2]
            a3 = adj_curr[3]
            n0 = inf
            n1 = inf
            n2 = inf
            n3 = inf

            if dp0 < inf:
                row0 = a0[b_idx]
                c00, c01, c02, c03 = row0
                base = dp0
                cost = base + c00
                if cost < n0:
                    n0 = cost
                cost = base + c01
                if cost < n1:
                    n1 = cost
                cost = base + c02
                if cost < n2:
                    n2 = cost
                cost = base + c03
                if cost < n3:
                    n3 = cost

            if dp1 < inf:
                row1 = a1[b_idx]
                c10, c11, c12, c13 = row1
                base = dp1
                cost = base + c10
                if cost < n0:
                    n0 = cost
                cost = base + c11
                if cost < n1:
                    n1 = cost
                cost = base + c12
                if cost < n2:
                    n2 = cost
                cost = base + c13
                if cost < n3:
                    n3 = cost

            if dp2 < inf:
                row2 = a2[b_idx]
                c20, c21, c22, c23 = row2
                base = dp2
                cost = base + c20
                if cost < n0:
                    n0 = cost
                cost = base + c21
                if cost < n1:
                    n1 = cost
                cost = base + c22
                if cost < n2:
                    n2 = cost
                cost = base + c23
                if cost < n3:
                    n3 = cost

            if dp3 < inf:
                row3 = a3[b_idx]
                c30, c31, c32, c33 = row3
                base = dp3
                cost = base + c30
                if cost < n0:
                    n0 = cost
                cost = base + c31
                if cost < n1:
                    n1 = cost
                cost = base + c32
                if cost < n2:
                    n2 = cost
                cost = base + c33
                if cost < n3:
                    n3 = cost

            dp0 = n0 + 1
            dp1 = n1 + 1
            dp2 = n2 + 1
            dp3 = n3 + 1
            curr_pos_idx = b_idx

            # --- 2. ボール -> かご ---
            adj_curr = adj[curr_pos_idx]
            a0 = adj_curr[0]
            a1 = adj_curr[1]
            a2 = adj_curr[2]
            a3 = adj_curr[3]
            n0 = inf
            n1 = inf
            n2 = inf
            n3 = inf

            if dp0 < inf:
                row0 = a0[bk_idx]
                c00, c01, c02, c03 = row0
                base = dp0
                cost = base + c00
                if cost < n0:
                    n0 = cost
                cost = base + c01
                if cost < n1:
                    n1 = cost
                cost = base + c02
                if cost < n2:
                    n2 = cost
                cost = base + c03
                if cost < n3:
                    n3 = cost

            if dp1 < inf:
                row1 = a1[bk_idx]
                c10, c11, c12, c13 = row1
                base = dp1
                cost = base + c10
                if cost < n0:
                    n0 = cost
                cost = base + c11
                if cost < n1:
                    n1 = cost
                cost = base + c12
                if cost < n2:
                    n2 = cost
                cost = base + c13
                if cost < n3:
                    n3 = cost

            if dp2 < inf:
                row2 = a2[bk_idx]
                c20, c21, c22, c23 = row2
                base = dp2
                cost = base + c20
                if cost < n0:
                    n0 = cost
                cost = base + c21
                if cost < n1:
                    n1 = cost
                cost = base + c22
                if cost < n2:
                    n2 = cost
                cost = base + c23
                if cost < n3:
                    n3 = cost

            if dp3 < inf:
                row3 = a3[bk_idx]
                c30, c31, c32, c33 = row3
                base = dp3
                cost = base + c30
                if cost < n0:
                    n0 = cost
                cost = base + c31
                if cost < n1:
                    n1 = cost
                cost = base + c32
                if cost < n2:
                    n2 = cost
                cost = base + c33
                if cost < n3:
                    n3 = cost

            dp0 = n0 + 1
            dp1 = n1 + 1
            dp2 = n2 + 1
            dp3 = n3 + 1
            curr_pos_idx = bk_idx

        result = min(dp0, dp1, dp2, dp3)
        score_calls += 1
        score_time += time.perf_counter() - st
        return result

    current_score = get_score(state)
    best_state = state[:]
    best_score = current_score

    # 焼きなましループ
    t_start = 15.0
    t_end = 0.05
    temp_ratio = math.log(t_end / t_start)
    iter_count = 0

    while True:
        total_elapsed = time.time() - start_time
        if total_elapsed > time_limit:
            break
        iter_count += 1
        t = t_start * math.exp(temp_ratio * total_elapsed / time_limit)

        mode = random.random()
        if mode < 0.4:
            i, j = random.sample(range(m), 2)
            state[i], state[j] = state[j], state[i]
            new_score = get_score(state)
            diff = current_score - new_score
            if diff >= 0 or random.random() < math.exp(diff / t):
                current_score = new_score
                if current_score < best_score:
                    best_score = current_score
                    best_state = state[:]
            else:
                state[i], state[j] = state[j], state[i]
        elif mode < 0.8:
            i = random.randrange(m)
            val = state.pop(i)
            j = random.randrange(m)
            state.insert(j, val)
            new_score = get_score(state)
            diff = current_score - new_score
            if diff >= 0 or random.random() < math.exp(diff / t):
                current_score = new_score
                if current_score < best_score:
                    best_score = current_score
                    best_state = state[:]
            else:
                state.pop(j)
                state.insert(i, val)
        else:
            i, j = sorted(random.sample(range(m), 2))
            state[i : j + 1] = state[i : j + 1][::-1]
            new_score = get_score(state)
            diff = current_score - new_score
            if diff >= 0 or random.random() < math.exp(diff / t):
                current_score = new_score
                if current_score < best_score:
                    best_score = current_score
                    best_state = state[:]
            else:
                state[i : j + 1] = state[i : j + 1][::-1]

    # -------------------------------------------------------------------------
    # 3. Free Transport を含むコマンド生成（SA の順列は固定）
    # -------------------------------------------------------------------------
    ball_pos = [balls[i] for i in range(m)]
    collected = [False] * m

    def get_path_with_macro(sr, sc, sd, tr, tc, td):
        """始点 (sr,sc,sd) から終点 (tr,tc,td) への最短経路 (マクロ FFF 優先) を返す"""
        dists = [[[10**9] * 4 for _ in range(n)] for _ in range(n)]
        parents = [[[None] * 4 for _ in range(n)] for _ in range(n)]
        queue = collections.deque([(sr, sc, sd)])
        dists[sr][sc][sd] = 0

        while queue:
            r, c, d = queue.popleft()
            if r == tr and c == tc and d == td:
                break
            curr_d = dists[r][c][d]

            # FFF を最優先
            r1, c1 = r + DR[d], c + DC[d]
            if 0 <= r1 < n and 0 <= c1 < n and can_move_forward(r, c, d):
                r2, c2 = r1 + DR[d], c1 + DC[d]
                if 0 <= r2 < n and 0 <= c2 < n and can_move_forward(r1, c1, d):
                    r3, c3 = r2 + DR[d], c2 + DC[d]
                    if 0 <= r3 < n and 0 <= c3 < n and can_move_forward(r2, c2, d):
                        if dists[r3][c3][d] > curr_d + 1:
                            dists[r3][c3][d] = curr_d + 1
                            parents[r3][c3][d] = (r, c, d, "FFF_TOKEN")
                            queue.append((r3, c3, d))

            # 通常 F
            if can_move_forward(r, c, d):
                nr, nc = r + DR[d], c + DC[d]
                if dists[nr][nc][d] > curr_d + 1:
                    dists[nr][nc][d] = curr_d + 1
                    parents[nr][nc][d] = (r, c, d, "F")
                    queue.append((nr, nc, d))

            # R, L
            for nd, cmd in [((d + 1) % 4, "R"), ((d - 1) % 4, "L")]:
                if dists[r][c][nd] > curr_d + 1:
                    dists[r][c][nd] = curr_d + 1
                    parents[r][c][nd] = (r, c, d, cmd)
                    queue.append((r, c, nd))

        path = []
        curr = (tr, tc, td)
        while parents[curr[0]][curr[1]][curr[2]] is not None:
            p = parents[curr[0]][curr[1]][curr[2]]
            path.append(p[3])
            curr = (p[0], p[1], p[2])
        return path[::-1]

    def get_shortest_path_to_cell(sr, sc, sd, tr, tc):
        """始点 (sr,sc,sd) からセル (tr,tc) への最短経路と到着時の向きを返す（マクロ FFF 対応）"""
        dists = [[[10**9] * 4 for _ in range(n)] for _ in range(n)]
        parents = [[[None] * 4 for _ in range(n)] for _ in range(n)]
        queue = collections.deque([(sr, sc, sd)])
        dists[sr][sc][sd] = 0

        while queue:
            r, c, d = queue.popleft()
            if r == tr and c == tc:
                path = []
                curr = (r, c, d)
                while parents[curr[0]][curr[1]][curr[2]] is not None:
                    p = parents[curr[0]][curr[1]][curr[2]]
                    path.append(p[3])
                    curr = (p[0], p[1], p[2])
                return path[::-1], d
            curr_d = dists[r][c][d]

            r1, c1 = r + DR[d], c + DC[d]
            if 0 <= r1 < n and 0 <= c1 < n and can_move_forward(r, c, d):
                r2, c2 = r1 + DR[d], c1 + DC[d]
                if 0 <= r2 < n and 0 <= c2 < n and can_move_forward(r1, c1, d):
                    r3, c3 = r2 + DR[d], c2 + DC[d]
                    if 0 <= r3 < n and 0 <= c3 < n and can_move_forward(r2, c2, d):
                        if dists[r3][c3][d] > curr_d + 1:
                            dists[r3][c3][d] = curr_d + 1
                            parents[r3][c3][d] = (r, c, d, "FFF_TOKEN")
                            queue.append((r3, c3, d))

            if can_move_forward(r, c, d):
                nr, nc = r + DR[d], c + DC[d]
                if dists[nr][nc][d] > curr_d + 1:
                    dists[nr][nc][d] = curr_d + 1
                    parents[nr][nc][d] = (r, c, d, "F")
                    queue.append((nr, nc, d))

            for nd, cmd in [((d + 1) % 4, "R"), ((d - 1) % 4, "L")]:
                if dists[r][c][nd] > curr_d + 1:
                    dists[r][c][nd] = curr_d + 1
                    parents[r][c][nd] = (r, c, d, cmd)
                    queue.append((r, c, nd))

        return [], sd

    # --- デバッグカウンタと移動コスト計測用 ---
    cand_total = 0
    cand_reject_detour = 0
    cand_reject_gain = 0
    cand_accept = 0
    gain_hist = collections.Counter()
    extra_hist = collections.Counter()

    free_transport_count = 0
    free_transport_gain = 0
    empty_move_cost = 0
    carry_move_cost = 0

    commands = []
    curr_r, curr_c = 0, 0
    curr_dir = 1

    for cur_k in best_state:
        # --- ピックアップ ---
        if not collected[cur_k]:
            target_r, target_c = ball_pos[cur_k]

            # 現在地から目標ボールへの直接コスト計算
            curr_idx = pos_to_idx[(curr_r, curr_c)]
            target_idx = pos_to_idx[(target_r, target_c)]
            direct_cost = min(adj_dist[curr_idx][curr_dir][target_idx][d] for d in range(4))

            # --- 無料輸送候補探索 ---
            best_candidate = None
            best_cand_gain = -(10**9)

            for X in range(m):
                if X == cur_k or collected[X] or ball_pos[X] is None:
                    continue
                X_pos = ball_pos[X]
                if X_pos not in pos_to_idx:
                    continue
                X_idx = pos_to_idx[X_pos]

                # 迂回コスト計算（候補Xを経由してcur_kへ）
                detour_min = INF
                best_d1 = -1
                best_d2 = -1
                for d1 in range(4):
                    cost1 = adj_dist[curr_idx][curr_dir][X_idx][d1]
                    if cost1 >= INF:
                        continue
                    for d2 in range(4):
                        cost2 = adj_dist[X_idx][d1][target_idx][d2]
                        if cost2 >= INF:
                            continue
                        total = cost1 + 1 + cost2 + 1  # +S×2
                        if total < detour_min:
                            detour_min = total
                            best_d1 = d1
                            best_d2 = d2

                if detour_min == INF:
                    continue

                extra_cost = detour_min - direct_cost
                cand_total += 1  # 候補として認識

                # 修正5：迂回制限を4に緩和
                if extra_cost > 4:
                    cand_reject_detour += 1
                    extra_hist[extra_cost] += 1
                    continue

                # 修正4：ゲイン計算（goalX基準）
                old_dist = min(adj_dist[X_idx][sd][pos_to_idx[baskets[X]]][dd] for sd in range(4) for dd in range(4))
                new_dist = min(
                    adj_dist[target_idx][sd][pos_to_idx[baskets[X]]][dd] for sd in range(4) for dd in range(4)
                )
                gain = old_dist - new_dist
                gain_hist[gain] += 1
                extra_hist[extra_cost] += 1

                # 修正4：cost = extra_cost、gain >= cost で採用
                cost = extra_cost
                if gain >= cost:
                    if gain > best_cand_gain:
                        best_cand_gain = gain
                        best_candidate = (X, best_d1, best_d2, gain)
                else:
                    cand_reject_gain += 1

            if best_candidate:
                X, d1, d2, gain = best_candidate
                X_pos = ball_pos[X]
                cand_accept += 1

                # Xへ移動 → S → cur_kの場所へ移動 → S
                path1 = get_path_with_macro(curr_r, curr_c, curr_dir, X_pos[0], X_pos[1], d1)
                commands.extend(path1)
                commands.append("S")
                empty_move_cost += len(path1)  # 空手移動（Xへ）

                ball_pos[X] = None
                curr_r, curr_c = X_pos
                curr_dir = d1

                path2 = get_path_with_macro(curr_r, curr_c, curr_dir, target_r, target_c, d2)
                commands.extend(path2)
                commands.append("S")
                # X を cur_k の場所に置き、cur_k を拾う
                ball_pos[X] = (target_r, target_c)
                ball_pos[cur_k] = None
                collected[cur_k] = True

                curr_r, curr_c = target_r, target_c
                curr_dir = d2
                free_transport_count += 1
                free_transport_gain += gain
            else:
                # 通常のピックアップ（空手移動）
                path, final_dir = get_shortest_path_to_cell(curr_r, curr_c, curr_dir, target_r, target_c)
                commands.extend(path)
                commands.append("S")
                empty_move_cost += len(path)  # 空手移動
                ball_pos[cur_k] = None
                collected[cur_k] = True
                curr_r, curr_c = target_r, target_c
                curr_dir = final_dir
        # else: already collected via free transport

        # --- デリバリー ---
        goal_r, goal_c = baskets[cur_k]
        path, final_dir = get_shortest_path_to_cell(curr_r, curr_c, curr_dir, goal_r, goal_c)
        commands.extend(path)
        commands.append("S")  # かごに置く（またはスワップ）
        carry_move_cost += len(path)  # ボール運搬移動
        curr_r, curr_c = goal_r, goal_c
        curr_dir = final_dir

    # -------------------------------------------------------------------------
    # 4. マクロ圧縮 (FFF_TOKEN → M/P)
    # -------------------------------------------------------------------------
    macro_count = commands.count("FFF_TOKEN")
    final_commands = []
    if macro_count >= 2:
        first = True
        for cmd in commands:
            if cmd == "FFF_TOKEN":
                if first:
                    final_commands.extend(["M", "F", "F", "F", "M"])
                    first = False
                else:
                    final_commands.append("P")
            else:
                final_commands.append(cmd)
    else:
        for cmd in commands:
            if cmd == "FFF_TOKEN":
                final_commands.extend(["F", "F", "F"])
            else:
                final_commands.append(cmd)

    # 出力
    sys.stdout.write("\n".join(final_commands) + "\n")

    # --- デバッグ情報 ---
    sys.stderr.write(
        f"Iterations: {iter_count}, "
        f"Score: {best_score}, "
        f"Total Commands: {len(final_commands)}, "
        f"FreeTransport: {free_transport_count}, Gain: {free_transport_gain}\n"
    )
    sys.stderr.write(f"BFS: {bfs_end_time - bfs_start_time:.3f}s, get_score: {score_time:.3f}s, calls: {score_calls}\n")
    sys.stderr.write(
        f"Candidates={cand_total} "
        f"DetourReject={cand_reject_detour} "
        f"GainReject={cand_reject_gain} "
        f"Accepted={cand_accept}\n"
    )
    sys.stderr.write(f"GainHist={dict(gain_hist)}\n")
    sys.stderr.write(f"ExtraHist={dict(extra_hist)}\n")
    sys.stderr.write(f"EmptyMove={empty_move_cost} CarryMove={carry_move_cost}\n")


if __name__ == "__main__":
    solve()
