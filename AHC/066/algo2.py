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
    # 1. 拡張BFSによる全点対最短経路・コスト計算
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

                # 【マクロ FFF 遷移】3歩前進
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

    # BFS の計測終了
    bfs_end_time = time.perf_counter()

    # -------------------------------------------------------------------------
    # 2. 焼きなまし法 (SA) による順列最適化
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
        dp0, dp1, dp2, dp3 = inf, 0, inf, inf
        curr_pos_idx = 0
        for idx in current_state:
            b_idx, bk_idx = balls_idx[idx], baskets_idx[idx]
            adj_curr = adj[curr_pos_idx]
            a0, a1, a2, a3 = adj_curr[0], adj_curr[1], adj_curr[2], adj_curr[3]
            n0 = n1 = n2 = n3 = inf
            if dp0 < inf:
                c00, c01, c02, c03 = a0[b_idx]
                if dp0 + c00 < n0:
                    n0 = dp0 + c00
                if dp0 + c01 < n1:
                    n1 = dp0 + c01
                if dp0 + c02 < n2:
                    n2 = dp0 + c02
                if dp0 + c03 < n3:
                    n3 = dp0 + c03
            if dp1 < inf:
                c10, c11, c12, c13 = a1[b_idx]
                if dp1 + c10 < n0:
                    n0 = dp1 + c10
                if dp1 + c11 < n1:
                    n1 = dp1 + c11
                if dp1 + c12 < n2:
                    n2 = dp1 + c12
                if dp1 + c13 < n3:
                    n3 = dp1 + c13
            if dp2 < inf:
                c20, c21, c22, c23 = a2[b_idx]
                if dp2 + c20 < n0:
                    n0 = dp2 + c20
                if dp2 + c21 < n1:
                    n1 = dp2 + c21
                if dp2 + c22 < n2:
                    n2 = dp2 + c22
                if dp2 + c23 < n3:
                    n3 = dp2 + c23
            if dp3 < inf:
                c30, c31, c32, c33 = a3[b_idx]
                if dp3 + c30 < n0:
                    n0 = dp3 + c30
                if dp3 + c31 < n1:
                    n1 = dp3 + c31
                if dp3 + c32 < n2:
                    n2 = dp3 + c32
                if dp3 + c33 < n3:
                    n3 = dp3 + c33
            dp0, dp1, dp2, dp3 = n0 + 1, n1 + 1, n2 + 1, n3 + 1
            curr_pos_idx = b_idx
            adj_curr = adj[curr_pos_idx]
            a0, a1, a2, a3 = adj_curr[0], adj_curr[1], adj_curr[2], adj_curr[3]
            n0 = n1 = n2 = n3 = inf
            if dp0 < inf:
                c00, c01, c02, c03 = a0[bk_idx]
                if dp0 + c00 < n0:
                    n0 = dp0 + c00
                if dp0 + c01 < n1:
                    n1 = dp0 + c01
                if dp0 + c02 < n2:
                    n2 = dp0 + c02
                if dp0 + c03 < n3:
                    n3 = dp0 + c03
            if dp1 < inf:
                c10, c11, c12, c13 = a1[bk_idx]
                if dp1 + c10 < n0:
                    n0 = dp1 + c10
                if dp1 + c11 < n1:
                    n1 = dp1 + c11
                if dp1 + c12 < n2:
                    n2 = dp1 + c12
                if dp1 + c13 < n3:
                    n3 = dp1 + c13
            if dp2 < inf:
                c20, c21, c22, c23 = a2[bk_idx]
                if dp2 + c20 < n0:
                    n0 = dp2 + c20
                if dp2 + c21 < n1:
                    n1 = dp2 + c21
                if dp2 + c22 < n2:
                    n2 = dp2 + c22
                if dp2 + c23 < n3:
                    n3 = dp2 + c23
            if dp3 < inf:
                c30, c31, c32, c33 = a3[bk_idx]
                if dp3 + c30 < n0:
                    n0 = dp3 + c30
                if dp3 + c31 < n1:
                    n1 = dp3 + c31
                if dp3 + c32 < n2:
                    n2 = dp3 + c32
                if dp3 + c33 < n3:
                    n3 = dp3 + c33
            dp0, dp1, dp2, dp3 = n0 + 1, n1 + 1, n2 + 1, n3 + 1
            curr_pos_idx = bk_idx
        res = min(dp0, dp1, dp2, dp3)
        score_calls += 1
        score_time += time.perf_counter() - st
        return res

    current_score = get_score(state)
    best_state, best_score = state[:], current_score
    t_start, t_end = 15.0, 0.05
    temp_ratio = math.log(t_end / t_start)
    iter_count = 0
    while True:
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            break
        iter_count += 1
        t = t_start * math.exp(temp_ratio * elapsed / time_limit)
        mode = random.random()
        if mode < 0.4:
            i, j = random.sample(range(m), 2)
            state[i], state[j] = state[j], state[i]
            new_score = get_score(state)
            if new_score < current_score or random.random() < math.exp((current_score - new_score) / t):
                current_score = new_score
                if current_score < best_score:
                    best_score, best_state = current_score, state[:]
            else:
                state[i], state[j] = state[j], state[i]
        elif mode < 0.8:
            i = random.randrange(m)
            val = state.pop(i)
            j = random.randrange(m)
            state.insert(j, val)
            new_score = get_score(state)
            if new_score < current_score or random.random() < math.exp((current_score - new_score) / t):
                current_score = new_score
                if current_score < best_score:
                    best_score, best_state = current_score, state[:]
            else:
                state.pop(j)
                state.insert(i, val)
        else:
            i, j = sorted(random.sample(range(m), 2))
            state[i : j + 1] = state[i : j + 1][::-1]
            new_score = get_score(state)
            if new_score < current_score or random.random() < math.exp((current_score - new_score) / t):
                current_score = new_score
                if current_score < best_score:
                    best_score, best_state = current_score, state[:]
            else:
                state[i : j + 1] = state[i : j + 1][::-1]

    # -------------------------------------------------------------------------
    # 3. リロケーションと経路復元
    # -------------------------------------------------------------------------
    def get_path_with_macro(sr, sc, sd, tr, tc, td):
        dists = [[[10**9] * 4 for _ in range(n)] for _ in range(n)]
        parents = [[[None] * 4 for _ in range(n)] for _ in range(n)]
        queue = collections.deque([(sr, sc, sd)])
        dists[sr][sc][sd] = 0
        while queue:
            r, c, d = queue.popleft()
            if r == tr and c == tc and d == td:
                break
            curr_d = dists[r][c][d]
            r1, c1 = r + DR[d], c + DC[d]
            if 0 <= r1 < n and 0 <= c1 < n and can_move_forward(r, c, d):
                r2, c2 = r1 + DR[d], c1 + DC[d]
                if 0 <= r2 < n and 0 <= c2 < n and can_move_forward(r1, c1, d):
                    r3, c3 = r2 + DR[d], c2 + DC[d]
                    if 0 <= r3 < n and 0 <= c3 < n and can_move_forward(r2, c2, d):
                        if dists[r3][c3][d] > curr_d + 1:
                            dists[r3][c3][d] = curr_d + 1
                            parents[r3][c3][d] = (r, c, d, "FFF")
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
        path, curr = [], (tr, tc, td)
        while parents[curr[0]][curr[1]][curr[2]] is not None:
            p = parents[curr[0]][curr[1]][curr[2]]
            path.append(p[3])
            curr = (p[0], p[1], p[2])
        return path[::-1]

    min_dist_table = [[INF] * num_unique for _ in range(num_unique)]
    for u in range(num_unique):
        for v in range(num_unique):
            d_min = INF
            for d1 in range(4):
                for d2 in range(4):
                    d = adj_dist[u][d1][v][d2]
                    if d < d_min:
                        d_min = d
            min_dist_table[u][v] = d_min

    centrality = []
    for u in range(num_unique):
        avg_d = sum(min_dist_table[u][basket_indices[k]] for k in range(m)) / m
        centrality.append((avg_d, u))
    centrality.sort()
    top_hubs = [idx for d, idx in centrality[:10]]

    relocations = {}  # step_idx -> (j_id, old_pos_idx, new_v_idx)
    current_ball_indices = ball_indices[:]
    curr_pos_idx = 0
    total_c = pos_g_c = adopted = gain_s = max_g = 0
    for i in range(m):
        best_j = best_v = max_gain = -1
        for k in range(1, 4):
            if i + k >= m:
                break
            j_id = best_state[i + k]
            pos_j_idx, target_j_idx = current_ball_indices[j_id], basket_indices[j_id]
            prev_j_bk_idx = basket_indices[best_state[i + k - 1]]
            candidates_v = [current_ball_indices[best_state[i]], basket_indices[best_state[i]]]
            if i + 1 < m:
                candidates_v.append(basket_indices[best_state[i + 1]])
            candidates_v.extend(top_hubs)
            seen_v = set()
            for v_idx in candidates_v:
                if v_idx in seen_v or v_idx == pos_j_idx:
                    continue
                seen_v.add(v_idx)
                total_c += 1
                inc = (
                    min_dist_table[curr_pos_idx][pos_j_idx]
                    + min_dist_table[pos_j_idx][v_idx]
                    + 2
                    - min_dist_table[curr_pos_idx][v_idx]
                )
                old_c = min_dist_table[prev_j_bk_idx][pos_j_idx] + min_dist_table[pos_j_idx][target_j_idx]
                new_c = min_dist_table[prev_j_bk_idx][v_idx] + min_dist_table[v_idx][target_j_idx]
                gain = old_c - new_c - inc
                if gain > 0:
                    pos_g_c += 1
                if gain > max_gain:
                    max_gain, best_j, best_v = gain, j_id, v_idx
        if best_j != -1 and max_gain > 5:
            relocations[i] = (best_j, current_ball_indices[best_j], best_v)
            current_ball_indices[best_j] = best_v
            adopted += 1
            gain_s += max_gain
            max_g = max(max_g, max_gain)
        curr_pos_idx = basket_indices[best_state[i]]
    sys.stderr.write(
        f"Relocation Stats: Candidates={total_c}, PositiveGain={pos_g_c}, Adopted={adopted}, AvgGain={gain_s / adopted if adopted > 0 else 0:.2f}, MaxGain={max_g}, MovedBalls={len(set(r[0] for r in relocations.values()))}\n"
    )
    ball_indices = current_ball_indices

    dp = [INF] * 4
    dp[1] = 0
    history = [(0, [INF, 0, INF, INF], [None] * 4)]
    curr_pos_idx = 0
    for idx in best_state:
        b_idx = ball_indices[idx]
        next_dp, best_prev = [INF] * 4, [None] * 4
        for d_in in range(4):
            if dp[d_in] > 10**8:
                continue
            for d_out in range(4):
                cost = adj_dist[curr_pos_idx][d_in][b_idx][d_out]
                if dp[d_in] + cost < next_dp[d_out]:
                    next_dp[d_out], best_prev[d_out] = dp[d_in] + cost, d_in
        history.append((b_idx, next_dp, best_prev))
        dp = [v + 1 for v in next_dp]
        curr_pos_idx = b_idx
        bk_idx = basket_indices[idx]
        next_dp, best_prev = [INF] * 4, [None] * 4
        for d_in in range(4):
            if dp[d_in] > 10**8:
                continue
            for d_out in range(4):
                cost = adj_dist[curr_pos_idx][d_in][bk_idx][d_out]
                if dp[d_in] + cost < next_dp[d_out]:
                    next_dp[d_out], best_prev[d_out] = dp[d_in] + cost, d_in
        history.append((bk_idx, next_dp, best_prev))
        dp = [v + 1 for v in next_dp]
        curr_pos_idx = bk_idx
    best_last_dir, min_final = 0, INF
    for d in range(4):
        if history[-1][1][d] < min_final:
            min_final, best_last_dir = history[-1][1][d], d
    optimal_dirs = [0] * len(history)
    curr_d = best_last_dir
    for i in range(len(history) - 1, 0, -1):
        optimal_dirs[i] = curr_d
        curr_d = history[i][2][curr_d]
    optimal_dirs[0] = 1

    full_commands_list = []
    for i in range(1, len(history)):
        src, dst = unique_positions[history[i - 1][0]], unique_positions[history[i][0]]
        step_idx = (i - 1) // 2
        if i % 2 == 1 and step_idx in relocations:
            _, p_j_idx, n_v_idx = relocations[step_idx]
            pos_j, n_v_pos = unique_positions[p_j_idx], unique_positions[n_v_idx]
            p1 = get_path_with_macro(src[0], src[1], optimal_dirs[i - 1], pos_j[0], pos_j[1], 0)
            for c in p1:
                full_commands_list.append("FFF_TOKEN" if c == "FFF" else c)
            full_commands_list.append("S")
            p2 = get_path_with_macro(pos_j[0], pos_j[1], 0, n_v_pos[0], n_v_pos[1], 0)
            for c in p2:
                full_commands_list.append("FFF_TOKEN" if c == "FFF" else c)
            full_commands_list.append("S")
            p3 = get_path_with_macro(n_v_pos[0], n_v_pos[1], 0, dst[0], dst[1], optimal_dirs[i])
            for c in p3:
                full_commands_list.append("FFF_TOKEN" if c == "FFF" else c)
        else:
            path = get_path_with_macro(src[0], src[1], optimal_dirs[i - 1], dst[0], dst[1], optimal_dirs[i])
            for c in path:
                full_commands_list.append("FFF_TOKEN" if c == "FFF" else c)
        full_commands_list.append("S")

    macro_count = full_commands_list.count("FFF_TOKEN")
    final_commands = []
    if macro_count >= 2:
        first = True
        for cmd in full_commands_list:
            if cmd == "FFF_TOKEN":
                if first:
                    final_commands.extend(["M", "F", "F", "F", "M"])
                    first = False
                else:
                    final_commands.append("P")
            else:
                final_commands.append(cmd)
    else:
        for cmd in full_commands_list:
            if cmd == "FFF_TOKEN":
                final_commands.extend(["F", "F", "F"])
            else:
                final_commands.append(cmd)
    sys.stdout.write("\n".join(final_commands) + "\n")
    sys.stderr.write(f"Iterations: {iter_count}, Score: {best_score}, Total Commands: {len(final_commands)}\n")
    sys.stderr.write(f"BFS: {bfs_end_time - bfs_start_time:.3f}s, get_score: {score_time:.3f}s, calls: {score_calls}\n")


if __name__ == "__main__":
    solve()
