import sys
import heapq
from collections import deque

# 定数
DIR_VALS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # R, D, L, U
DIR_CMDS = ["R", "D", "L", "U"]


class Solver:
    def __init__(self):
        # 入力
        input_data = sys.stdin.read().split()
        if not input_data:
            return
        it = iter(input_data)

        self.N = int(next(it))
        self.M = int(next(it))
        self.T = int(next(it))

        self.adj = [[] for _ in range(self.N * self.N)]
        self.v_walls = [next(it) for _ in range(self.N)]
        self.h_walls = [next(it) for _ in range(self.N - 1)]

        self.balls_init = []
        self.baskets = []
        for i in range(self.M):
            br = int(next(it))
            bc = int(next(it))
            dr = int(next(it))
            dc = int(next(it))
            self.balls_init.append(br * self.N + bc)
            self.baskets.append(dr * self.N + dc)

        self._build_graph()
        self.dist_matrix = self._precompute_all_pairs_dist()

    def _build_graph(self):
        for r in range(self.N):
            for c in range(self.N):
                u = r * self.N + c
                # Right
                if c < self.N - 1 and self.v_walls[r][c] == "0":
                    v = r * self.N + (c + 1)
                    self.adj[u].append(v)
                    self.adj[v].append(u)
                # Down
                if r < self.N - 1 and self.h_walls[r][c] == "0":
                    v = (r + 1) * self.N + c
                    self.adj[u].append(v)
                    self.adj[v].append(u)

    def _precompute_all_pairs_dist(self):
        """全てのセル(r,c)間の最短距離と経路を計算"""
        # dist[start_node][target_cell] = (distance, first_move_to_v)
        dist = [[(999, -1) for _ in range(self.N * self.N)] for _ in range(self.N * self.N)]
        for start in range(self.N * self.N):
            dist[start][start] = (0, -1)
            queue = deque([start])
            while queue:
                u = queue.popleft()
                d, _ = dist[start][u]
                for v in self.adj[u]:
                    if dist[start][v][0] == 999:
                        dist[start][v] = (d + 1, u)  # 逆向きに辿るため親を保持
                        queue.append(v)
        return dist

    def get_path_commands(self, start_pos, start_dir, target_pos):
        """start_pos(dir)からtarget_posへ移動するための最小コマンド列を生成"""
        if start_pos == target_pos:
            return [], start_dir

        # 経路復元
        path = []
        curr = target_pos
        while curr != start_pos:
            path.append(curr)
            curr = self.dist_matrix[start_pos][curr][1]
        path.reverse()

        cmds = []
        curr_dir = start_dir
        curr_pos = start_pos
        for next_pos in path:
            dr = (next_pos // self.N) - (curr_pos // self.N)
            dc = (next_pos % self.N) - (curr_pos % self.N)
            target_dir = -1
            for i, (tr, tc) in enumerate(DIR_VALS):
                if (dr, dc) == (tr, tc):
                    target_dir = i
                    break

            # 回転
            while curr_dir != target_dir:
                diff = (target_dir - curr_dir) % 4
                if diff == 1:
                    cmds.append("R")
                    curr_dir = (curr_dir + 1) % 4
                elif diff == 3:
                    cmds.append("L")
                    curr_dir = (curr_dir - 1) % 4
                else:
                    cmds.append("R")
                    curr_dir = (curr_dir + 1) % 4
            cmds.append("F")
            curr_pos = next_pos

        return cmds, curr_dir

    def solve(self):
        # Beam Search State:
        # (score, robot_pos, robot_dir, held_ball, floor_balls_tuple, delivered_mask, history_str)
        # score = g_score + h_score

        # 初期状態: 全てのボールは初期位置
        initial_floor_balls = tuple(self.balls_init)

        # beam[delivered_count] = [states]
        beam_width = 100  # メモリ節約のため少し絞る
        buckets = [[] for _ in range(self.M + 1)]

        # history を文字列にしてメモリを節約
        start_state = (0, 0, 0, -1, initial_floor_balls, 0, "")
        buckets[0].append(start_state)

        best_full_sequence = None

        for d_count in range(self.M + 1):
            if not buckets[d_count]:
                continue

            # 評価値でソートして絞り込み
            buckets[d_count].sort(key=lambda x: x[0])
            buckets[d_count] = buckets[d_count][:beam_width]

            # 同一 bucket 内での無限増殖を防ぐため、処理済み件数を制限
            processed_count = 0
            while processed_count < len(buckets[d_count]):
                state = buckets[d_count][processed_count]
                processed_count += 1
                if processed_count > beam_width * 5:
                    break  # 探索幅の5倍まで

                score, pos, direction, held, floor_balls, delivered_mask, history = state

                # ミッション生成
                if held == -1:
                    # 1. 床にあるボールを拾いに行く
                    for i in range(self.M):
                        if not (delivered_mask & (1 << i)) and floor_balls[i] != -1:
                            target_pos = floor_balls[i]
                            move_cmds, next_dir = self.get_path_commands(pos, direction, target_pos)
                            new_history = history + "".join(move_cmds) + "S"
                            new_floor = list(floor_balls)
                            new_floor[i] = -1

                            new_g = len(new_history)
                            new_h = self._calc_heuristic(target_pos, i, new_floor, delivered_mask)
                            new_state = (
                                new_g + new_h,
                                target_pos,
                                next_dir,
                                i,
                                tuple(new_floor),
                                delivered_mask,
                                new_history,
                            )
                            buckets[d_count].append(new_state)
                else:
                    # 2. 持っているボールをバスケットに届ける
                    target_basket = self.baskets[held]
                    move_cmds, next_dir = self.get_path_commands(pos, direction, target_basket)
                    new_history = history + "".join(move_cmds) + "S"
                    new_delivered = delivered_mask | (1 << held)
                    new_floor = floor_balls  # heldはすでに-1

                    new_g = len(new_history)
                    if d_count + 1 == self.M:
                        if best_full_sequence is None or new_g < len(best_full_sequence):
                            best_full_sequence = new_history
                    else:
                        new_h = self._calc_heuristic(target_basket, -1, new_floor, new_delivered)
                        new_state = (new_g + new_h, target_basket, next_dir, -1, new_floor, new_delivered, new_history)
                        buckets[d_count + 1].append(new_state)

                    # 3. 持っているボールを床の別のボールと交換する (Relay!)
                    for i in range(self.M):
                        if i != held and not (delivered_mask & (1 << i)) and floor_balls[i] != -1:
                            target_pos = floor_balls[i]
                            move_cmds, next_dir = self.get_path_commands(pos, direction, target_pos)
                            new_history = history + "".join(move_cmds) + "S"
                            new_floor = list(floor_balls)
                            new_floor[i] = -1
                            new_floor[held] = target_pos  # 持っていたボールをそこに置く

                            new_g = len(new_history)
                            new_h = self._calc_heuristic(target_pos, i, new_floor, delivered_mask)
                            new_state = (
                                new_g + new_h,
                                target_pos,
                                next_dir,
                                i,
                                tuple(new_floor),
                                delivered_mask,
                                new_history,
                            )
                            buckets[d_count].append(new_state)

        return self._compress_macros(best_full_sequence)

    def _calc_heuristic(self, robot_pos, held_ball, floor_balls, delivered_mask):
        """
        現在の状態から全納品までの残りコスト推定
        """
        h = 0
        # まだ運んでいないボールについて、現在位置からバスケットまでの距離を合算
        for i in range(self.M):
            if not (delivered_mask & (1 << i)):
                if i == held_ball:
                    h += self.dist_matrix[robot_pos][self.baskets[i]][0]
                elif floor_balls[i] != -1:
                    h += self.dist_matrix[floor_balls[i]][self.baskets[i]][0]
        return int(h * 1.1)  # 少し重みをつけて貪欲性を増す

    def _compress_macros(self, commands):
        """
        簡易的なマクロ圧縮 (M, Pの適用)
        "FFF" を探して、2回以上出現するならマクロ化する
        """
        if not commands:
            return []

        # commands は文字列を想定
        fff_count = commands.count("FFF")

        if fff_count < 2:
            return list(commands)

        res = []
        i = 0
        first_fff = True
        while i < len(commands):
            if i + 2 < len(commands) and commands[i : i + 3] == "FFF":
                if first_fff:
                    # 初回はマクロ登録兼実行
                    res.extend(["M", "F", "F", "F", "M"])
                    first_fff = False
                else:
                    # 2回目以降は再生
                    res.append("P")
                i += 3
            else:
                res.append(commands[i])
                i += 1
        return res


def main():
    solver = Solver()
    result = solver.solve()
    for cmd in result:
        print(cmd)


if __name__ == "__main__":
    main()
