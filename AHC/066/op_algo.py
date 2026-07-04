"""
Optuna を使ったパラメータチューニングを行うためのコード。
内容はalgo.pyと同様で、チューニングをしやすくしている。

ジャッジへの提出は出来ない。
"""

import sys
import collections
import os
import time
import random

# 定数
DR = (-1, 0, 1, 0)  # 上, 右, 下, 左
DC = (0, 1, 0, -1)
DIR_NAMES = ["U", "R", "D", "L"]
INF = 10**9


def _env_int(name, default):
    value = os.environ.get(name)
    return default if value is None else int(value)


def _env_float(name, default):
    value = os.environ.get(name)
    return default if value is None else float(value)


def solve():
    # 1. プログラム全体の開始時刻を記録
    start_time = time.time()
    # BFS の計測開始時刻を記録
    bfs_start_time = time.perf_counter()
    time_limit = _env_float("OP_TIME_LIMIT", 1.75)  # ジャッジのブレを考慮したチキンレース

    random_seed = _env_int("OP_RANDOM_SEED", 42)
    beam_width_early = _env_int("OP_BEAM_WIDTH_EARLY", 100)
    beam_width_mid = _env_int("OP_BEAM_WIDTH_MID", 70)
    beam_width_late = _env_int("OP_BEAM_WIDTH_LATE", 40)
    beam_threshold_1 = _env_int("OP_BEAM_THRESHOLD_1", 33)
    beam_threshold_2 = _env_int("OP_BEAM_THRESHOLD_2", 66)
    if beam_threshold_1 > beam_threshold_2:
        beam_threshold_1, beam_threshold_2 = beam_threshold_2, beam_threshold_1
    candidate_limit = max(1, _env_int("OP_CANDIDATE_LIMIT", 5))
    rollout_short_k = max(1, _env_int("OP_ROLLOUT_K_SHORT", 2))
    rollout_long_k = max(rollout_short_k, _env_int("OP_ROLLOUT_K_LONG", 3))
    rollout_long_prob = min(1.0, max(0.0, _env_float("OP_ROLLOUT_PROB_LONG", 0.1)))
    macro_min_count = max(1, _env_int("OP_MACRO_MIN_COUNT", 2))

    random.seed(random_seed)  # 再現性のための固定シード

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

    # 近傍リスト（単純距離順）
    nearest_balls = [sorted(range(m), key=lambda b: dist_combined[i][b]) for i in range(num_unique)]

    def simulate(curr_pos_idx, curr_dir, visited_mask, k):
        """未来 K 手のコストを貪欲にシミュレーション"""
        total = 0
        curr_pos = curr_pos_idx
        curr_mask = visited_mask
        # 方向は簡易的に dist_min を使用するが、ロールアウトの定義に従いコストを積算
        for _ in range(k):
            best_b = -1
            # 近傍リストから未訪問のものを探す
            for b_idx in nearest_balls[curr_pos]:
                if not (curr_mask & (1 << b_idx)):
                    best_b = b_idx
                    break
            if best_b == -1:
                break
            total += dist_combined[curr_pos][best_b]
            curr_pos = basket_indices[best_b]
            curr_mask |= 1 << best_b
        return total

    # 定数 (時間依存の制御用)
    ROLL_K_MAX = 10
    ROLL_K_MIN = 2
    HEURISTIC_WEIGHT = 0.5

    def get_rollout_k(start_time, time_limit):
        t = time.time() - start_time
        ratio = t / time_limit
        # 序盤は深く見る、終盤は浅く
        return int(ROLL_K_MAX - (ROLL_K_MAX - ROLL_K_MIN) * ratio)

    def get_beam_width(level, beam_threshold_1, beam_threshold_2, beam_width_early, beam_width_mid, beam_width_late):
        if level < beam_threshold_1:
            return beam_width_early
        elif level < beam_threshold_2:
            return beam_width_mid
        return beam_width_late

    def evaluate_state(curr_pos_idx, mask, start_time, time_limit, m, dist_combined):
        k = get_rollout_k(start_time, time_limit)
        best = INF
        for b in range(m):
            if not (mask & (1 << b)):
                c = dist_combined[curr_pos_idx][b]
                if c < best:
                    best = c
        # 未訪問がなければ0を返す
        if best == INF:
            return 0
        return best * k

    # ビームサーチの状態: (評価スコア, (精密DPコスト配列), 現在位置idx, 訪問済みmask, 訪問順路)
    # 評価スコア = 精密DPコスト + HEURISTIC_WEIGHT * 未来評価
    # 初期状態: (0,0) 右向き(1), コスト0
    initial_dists = [INF, 0, INF, INF]
    beam = [(0, initial_dists, 0, 0, [])]

    # ビームサーチ本体
    for level in range(m):
        # 経過時間による打ち切り
        if time.time() - start_time > time_limit:
            break

        # 動的ビーム幅の決定
        W = get_beam_width(level, beam_threshold_1, beam_threshold_2, beam_width_early, beam_width_mid, beam_width_late)

        next_beam_candidates = []

        for _, curr_dists, curr_pos_idx, mask, path in beam:
            # 未訪問ボールの中から、単純距離が近い上位 B 件 + ランダム 1 件を抽出
            candidates = []
            for b_idx in nearest_balls[curr_pos_idx]:
                if not (mask & (1 << b_idx)):
                    candidates.append(b_idx)
                    if len(candidates) >= candidate_limit:
                        break

            # ランダムな候補を1件追加
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
                        c = base + row[d_out]
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
                        c = base + row[d_out]
                        if c < nn_costs[d_out]:
                            nn_costs[d_out] = c
                # basket に置く (+1)
                for d in range(4):
                    nn_costs[d] += 1

                new_cost = min(nn_costs)

                # --- 2. 軽量ヒューリスティックによる未来予測 ---
                future_cost = evaluate_state(bk_idx, mask | (1 << b_idx), start_time, time_limit, m, dist_combined)

                score = new_cost + HEURISTIC_WEIGHT * future_cost
                next_beam_candidates.append((score, nn_costs, bk_idx, mask | (1 << b_idx), path + [b_idx]))

        # 次のビームを決定 (スコア順)
        next_beam_candidates.sort(key=lambda x: x[0])

        # 同一状態 (mask) の重複排除
        seen_masks = set()
        beam = []
        for cand in next_beam_candidates:
            if cand[3] not in seen_masks:
                seen_masks.add(cand[3])
                beam.append(cand)
                if len(beam) >= W:
                    break

        if not beam:
            break

    # 最良の順列を選択
    best_state = beam[0][4]
    best_score = min(beam[0][1])
    iter_count = level + 1  # ビームサーチのステップ数  # type: ignore[reportArgumentType]

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
    if macro_count >= macro_min_count:
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
