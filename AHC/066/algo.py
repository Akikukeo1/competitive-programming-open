"""
テスト中の新アルゴリズム。
"""

import sys
import collections
import time
import random

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

    # 最適化可能なパラメータ
    TIME_LIMIT = 1.75
    SEED = 42

    # ビーム
    BEAM_WIDTH_EARLY = 140
    BEAM_WIDTH_MID = 80
    BEAM_WIDTH_LATE = 40

    BEAM_THRESHOLD_1 = 15
    BEAM_THRESHOLD_2 = 60

    # 候補
    CANDIDATE_LIMIT = 8

    # ロールアウト
    ROLL_K_MAX = 3
    ROLL_K_MIN = 1

    # マクロ
    MACRO_MIN_COUNT = 2

    # 評価重み
    # HEURISTIC_WEIGHT = 1.0
    DIRECTION_WEIGHT = 2.0

    random.seed(SEED)  # 再現性のための固定シード

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
    # 2. ビームサーチによる順列最適化（ロールアウト評価・動的ビーム幅・探索の揺らぎ）
    # -------------------------------------------------------------------------
    ball_indices = [pos_to_idx[p] for p in balls]
    basket_indices = [pos_to_idx[p] for p in baskets]

    # 方向不問の最小距離テーブル（評価用）
    dist_min = [[INF] * num_unique for _ in range(num_unique)]
    for i in range(num_unique):
        for j in range(num_unique):
            val = INF
            for sd in range(4):
                row = adj_dist[i][sd][j]
                v = min(row)
                if v < val:
                    val = v
            dist_min[i][j] = val

    # ball -> basket の一連の最小コスト
    dist_ball_total = [dist_min[ball_indices[i]][basket_indices[i]] + 2 for i in range(m)]

    # dist_combined[from_pos][b_idx]: from_pos からボール b_idx を拾い、かごへ届ける最小コスト
    dist_combined = [[0] * m for _ in range(num_unique)]
    for i in range(num_unique):
        for b_idx in range(m):
            dist_combined[i][b_idx] = dist_min[i][ball_indices[b_idx]] + dist_ball_total[b_idx]

    # 近傍リスト（単純距離順から、設計に基づくスコア付きへ変更）
    def get_candidate_score(curr_pos_idx, curr_dir, b_idx):
        dist_to_ball = dist_min[curr_pos_idx][ball_indices[b_idx]]
        dist_ball_to_basket = dist_ball_total[b_idx]

        # 方向ペナルティ（簡易版）
        ball_pos = balls[b_idx]
        curr_pos = unique_positions[curr_pos_idx]
        dx = ball_pos[1] - curr_pos[1]
        dy = ball_pos[0] - curr_pos[0]

        # 向きの正規化とドット積
        dot = (dx * DR[curr_dir] + dy * DC[curr_dir]) / (max(1, abs(dx) + abs(dy)))
        penalty = 1 - max(0, dot)

        return 1.0 * dist_to_ball + 1.0 * dist_ball_to_basket + DIRECTION_WEIGHT * penalty

    # -------------------------------------------------------------------------
    # 補助関数: 時間依存パラメータ
    # -------------------------------------------------------------------------
    def get_rollout_k(start_time, time_limit):
        t = time.time() - start_time
        ratio = min(1.0, t / time_limit)
        # 序盤は深く見る、終盤は浅く
        return int(ROLL_K_MAX - (ROLL_K_MAX - ROLL_K_MIN) * ratio)

    def get_beam_width(level):
        if level < BEAM_THRESHOLD_1:
            return BEAM_WIDTH_EARLY
        elif level < BEAM_THRESHOLD_2:
            return BEAM_WIDTH_MID
        return BEAM_WIDTH_LATE

    # -------------------------------------------------------------------------
    # 3. 新評価関数（軽量ヒューリスティック）
    # -------------------------------------------------------------------------
    def evaluate_state(curr_pos_idx, mask, *args):
        scores = []

        for b in range(m):
            if mask & (1 << b):
                continue

            base = dist_combined[curr_pos_idx][b]

            pos_after = ball_indices[b]

            future_options = 0
            for bb in range(m):
                if mask & (1 << bb) or bb == b:
                    continue
                if dist_combined[pos_after][bb] < base:
                    future_options += 1

            scores.append(base - 0.2 * future_options)

        if not scores:
            return 0  # ← ここが重要（全消し対策）

        return min(scores)

    # ビームサーチの状態: (評価スコア, (精密DPコスト配列), 現在位置idx, 訪問済みmask, 訪問順路)
    initial_dists = [INF, 0, INF, INF]
    beam = [(0, initial_dists, 0, 0, [])]

    # ビームサーチ本体
    for level in range(m):
        # 経過時間による打ち切り
        if time.time() - start_time > TIME_LIMIT:
            break

        # 動的ビーム幅の決定
        W = get_beam_width(level)

        next_beam_candidates = []

        for _, curr_dists, curr_pos_idx, mask, path in beam:
            # 未訪問ボールの中から、スコアが良い上位 B 件 + ランダム 1 件を抽出
            scored_candidates = []

            # 最適な方向を推定（コストが最小の方向を採用）
            best_dir = min(range(4), key=lambda d: curr_dists[d])

            for b_idx in range(m):
                if not (mask & (1 << b_idx)):
                    score = get_candidate_score(curr_pos_idx, best_dir, b_idx)
                    scored_candidates.append((score, b_idx))

            scored_candidates.sort(key=lambda x: x[0])
            candidates = [x[1] for x in scored_candidates[:CANDIDATE_LIMIT]]

            # ランダムな候補を1件追加（多様性の確保）
            others = [b for b in range(m) if not (mask & (1 << b)) and b not in candidates]
            if others:
                candidates.append(random.choice(others))

            for b_idx in candidates:
                # --- 1. 精密DPによる現在コストの計算 ---
                bk_idx = basket_indices[b_idx]

                # ball に到達
                adj_b = adj_dist[curr_pos_idx]
                n_costs = [INF] * 4

                for d_in in range(4):
                    if curr_dists[d_in] == INF:
                        continue
                    row = adj_b[d_in][ball_indices[b_idx]]
                    base = curr_dists[d_in]
                    for d_out in range(4):
                        directional_gain = row[d_out] - dist_min[curr_pos_idx][ball_indices[b_idx]]
                        c = base + row[d_out] + (DIRECTION_WEIGHT / 2.0) * directional_gain
                        if c < n_costs[d_out]:
                            n_costs[d_out] = c
                # ball を拾う (+1)
                for d in range(4):
                    n_costs[d] += 1

                # basket に到達
                adj_bk = adj_dist[ball_indices[b_idx]]
                nn_costs = [INF] * 4
                for d_in in range(4):
                    if n_costs[d_in] == INF:
                        continue
                    row = adj_bk[d_in][bk_idx]
                    base = n_costs[d_in]
                    for d_out in range(4):
                        directional_gain = row[d_out] - dist_min[ball_indices[b_idx]][bk_idx]
                        c = base + row[d_out] + (DIRECTION_WEIGHT / 2.0) * directional_gain
                        if c < nn_costs[d_out]:
                            nn_costs[d_out] = c
                # basket に置く (+1)
                for d in range(4):
                    nn_costs[d] += 1

                new_cost = min(nn_costs)

                # --- 2. 新評価関数による未来予測 ---
                future_cost = evaluate_state(bk_idx, mask | (1 << b_idx), level, start_time, TIME_LIMIT)

                score = new_cost + future_cost
                next_beam_candidates.append((score, nn_costs, bk_idx, mask | (1 << b_idx), path + [b_idx]))

        # 次のビームを決定 (スコア順)
        next_beam_candidates.sort(key=lambda x: x[0])

        # 同一状態 (mask) の重複排除 (緩和: 上位2件まで許可)
        mask_counts = collections.defaultdict(int)
        beam = []
        for cand in next_beam_candidates:
            if mask_counts[cand[3]] < 2:
                mask_counts[cand[3]] += 1
                beam.append(cand)
                if len(beam) >= W:
                    break

        if not beam:
            break

    # 最良の順列を選択
    best_state = beam[0][4]
    best_score = min(beam[0][1])
    iter_count = level + 1  # type: ignore[reportUndefinedVariable]

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
    # 4. FFF 限定マクロ置換
    # -------------------------------------------------------------------------
    macro_count = full_commands_list.count("FFF_TOKEN")
    final_commands = []

    # 2回以上登場するなら、マクロ化した方が確実にお得（または同等）
    if macro_count >= MACRO_MIN_COUNT:
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
        # 1回しか出ないならマクロにする意味がないので通常の F F F に戻す
        for cmd in full_commands_list:
            if cmd == "FFF_TOKEN":
                final_commands.extend(["F", "F", "F"])
            else:
                final_commands.append(cmd)

    # 出力
    sys.stdout.write("\n".join(final_commands) + "\n")
    # 実行全体の統計を stderr に出す
    sys.stderr.write(f"Iterations: {iter_count}, Score: {best_score}, Total Commands: {len(final_commands)}\n")

    # BFS と get_score の計測結果を stderr に出す
    sys.stderr.write(f"BFS: {bfs_end_time - bfs_start_time:.3f}s, get_score: {score_time:.3f}s, calls: {score_calls}\n")


if __name__ == "__main__":
    solve()
