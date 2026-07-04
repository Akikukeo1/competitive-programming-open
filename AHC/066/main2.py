import sys
import collections
import time
import random
import math
from collections import Counter

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
        # 外側の計測変数を更新する
        nonlocal score_calls, score_time

        # get_score の計測開始時刻を記録する
        st = time.perf_counter()

        # 参照をローカルに束縛する
        adj = adj_dist
        balls_idx = ball_indices
        baskets_idx = basket_indices
        inf = INF

        # 4 変数で DP を持つ
        dp0 = inf
        dp1 = 0  # 初期状態: (0,0) で右向き (1)
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

        # スコアを確定する
        result = min(dp0, dp1, dp2, dp3)

        # 呼び出し回数を加算する
        score_calls += 1

        # get_score の累積時間を加算する
        score_time += time.perf_counter() - st

        # 計測後のスコアを返す
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
        # 経過時間をプログラムの開始から正確に測る
        total_elapsed = time.time() - start_time
        if total_elapsed > time_limit:
            break  # 規定秒を超えたら、脱出！

        iter_count += 1

        # 温度の減衰率（時間ベース）
        t = t_start * math.exp(temp_ratio * total_elapsed / time_limit)

        # 近傍操作: Swap / Insert / Reverse
        mode = random.random()
        if mode < 0.4:  # Swap (小さい局所交換)
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
        elif mode < 0.8:  # Insert (要素を1つ移動)
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
        else:  # Reverse (区間反転)
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
    # 3. 最良の順列から操作列を復元（FFF 優先の拡張BFS）
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

            # 復元時は FFF を最優先で探索させて、積極的に踏ませる！
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

            # 通常の F
            if can_move_forward(r, c, d):
                nr, nc = r + DR[d], c + DC[d]
                if dists[nr][nc][d] > curr_d + 1:
                    dists[nr][nc][d] = curr_d + 1
                    parents[nr][nc][d] = (r, c, d, "F")
                    queue.append((nr, nc, d))

            # 通常の R, L
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

    # 各地点での最適な向きを逆算（確定フェーズ）
    dp = [10**9] * 4
    dp[1] = 0
    history = [(0, [10**9, 0, 10**9, 10**9], [None] * 4)]

    curr_pos_idx = 0
    for idx in best_state:
        b_idx = ball_indices[idx]
        next_dp, best_prev = [10**9] * 4, [None] * 4
        adj_curr = adj_dist[curr_pos_idx]
        for d_in in range(4):
            if dp[d_in] > 10**8:
                continue
            for d_out in range(4):
                cost = adj_curr[d_in][b_idx][d_out]
                if dp[d_in] + cost < next_dp[d_out]:
                    next_dp[d_out] = dp[d_in] + cost
                    best_prev[d_out] = d_in  # type: ignore[reportArgumentType]
        history.append((b_idx, next_dp, best_prev))
        dp = [v + 1 for v in next_dp]
        curr_pos_idx = b_idx

        bk_idx = basket_indices[idx]
        next_dp, best_prev = [10**9] * 4, [None] * 4
        adj_curr = adj_dist[curr_pos_idx]
        for d_in in range(4):
            if dp[d_in] > 10**8:
                continue
            for d_out in range(4):
                cost = adj_curr[d_in][bk_idx][d_out]
                if dp[d_in] + cost < next_dp[d_out]:
                    next_dp[d_out] = dp[d_in] + cost
                    best_prev[d_out] = d_in  # type: ignore[reportArgumentType]
        history.append((bk_idx, next_dp, best_prev))
        dp = [v + 1 for v in next_dp]
        curr_pos_idx = bk_idx

    optimal_dirs = [0] * len(history)
    best_last_dir = 0
    min_final = 10**9
    for d in range(4):
        if history[-1][1][d] < min_final:
            min_final = history[-1][1][d]
            best_last_dir = d

    curr_d = best_last_dir
    for i in range(len(history) - 1, 0, -1):
        optimal_dirs[i] = curr_d
        curr_d = history[i][2][curr_d]
    optimal_dirs[0] = 1

    # 経路復元トークン配列の構築
    full_commands_list = []
    for i in range(1, len(history)):
        src_pos = unique_positions[history[i - 1][0]]
        dst_pos = unique_positions[history[i][0]]
        path = get_path_with_macro(src_pos[0], src_pos[1], optimal_dirs[i - 1], dst_pos[0], dst_pos[1], optimal_dirs[i])
        for cmd in path:
            if cmd == "FFF":
                full_commands_list.append("FFF_TOKEN")  # 一時的な目印
            else:
                full_commands_list.append(cmd)
        full_commands_list.append("S")

    # -------------------------------------------------------------------------
    # 4. 動的マクロ探索
    # -------------------------------------------------------------------------

    # FFF_TOKEN を展開
    expanded = []

    for cmd in full_commands_list:
        if cmd == "FFF_TOKEN":
            expanded.extend(["F", "F", "F"])
        else:
            expanded.append(cmd)

    best_pattern = None
    best_gain = 0

    MAX_LEN = 8

    for length in range(2, MAX_LEN + 1):
        counter = Counter()

        for i in range(len(expanded) - length + 1):
            pat = tuple(expanded[i : i + length])

            counter[pat] += 1

        for pat, freq in counter.items():
            if freq < 2:
                continue

            L = len(pat)

            gain = freq * (L - 1) - (L + 2)

            if gain > best_gain:
                best_gain = gain
                best_pattern = pat

    # 圧縮
    if best_pattern is not None and best_gain > 0:
        final_commands = []

        # マクロ定義
        final_commands.append("M")

        for x in best_pattern:
            final_commands.append(x)

        final_commands.append("M")

        pattern_len = len(best_pattern)

        i = 0

        while i < len(expanded):
            if i + pattern_len <= len(expanded) and tuple(expanded[i : i + pattern_len]) == best_pattern:
                final_commands.append("P")
                i += pattern_len
            else:
                final_commands.append(expanded[i])
                i += 1

    else:
        final_commands = expanded

    sys.stdout.write("".join(final_commands))

    # デバッグ
    if best_pattern is not None:
        sys.stderr.write(f"Macro={''.join(best_pattern)} Gain={best_gain} Len={len(best_pattern)}\n")
    else:
        sys.stderr.write("Macro=None\n")


if __name__ == "__main__":
    solve()
