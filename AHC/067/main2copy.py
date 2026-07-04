import sys
import time
import random
from collections import deque

# ============================================================
# NOTE: 壁は fixed_walls と movable_walls の2種類に分けて管理する。
#   fixed_walls  : スイッチ部屋・ゴール封鎖・チェーン構造を守る壁 (絶対不変)
#   movable_walls: 焼きなましで追加・移動・削除できる迷路用の壁
#
# 元のマップ c[i][j] == '#' のマス(固定障害物)は別扱いで、
# 上記のセットには含まない。
# BFS 時は c の '#' + fixed_walls + movable_walls を合わせて壁扱いする。
# ============================================================


def calc_T(N, K, c, fixed_walls, movable_walls, door_h, door_v, switch):
    """スタート(0,0)からゴール(N-1,N-1)までの最短距離を BFS で返す。
    壁判定: c[i][j]=='#' または (i,j) が fixed_walls/movable_walls に含まれる。
    """

    def is_wall(i, j):
        return c[i][j] == "#" or (i, j) in fixed_walls or (i, j) in movable_walls

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
            if not (0 <= ni < N and 0 <= nj < N) or is_wall(ni, nj):
                continue

            # ドア判定
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

        # スイッチを踏む
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
    # NOTE: c は str のリストとして保持。壁判定は fixed_walls / movable_walls で行うため、
    #       c 自体は変更しない（元の障害物 '#' だけを参照する）。
    c = list(input_data[3 : 3 + N])

    # 元のマップにおける通路セル
    empty_cells = [(i, j) for i in range(N) for j in range(N) if c[i][j] == "."]

    # ドア・スイッチの初期化
    door_h = [[-1] * N for _ in range(N)]  # (i,j)→(i+1,j) 間のドア
    door_v = [[-1] * N for _ in range(N)]  # (i,j)→(i,j+1) 間のドア
    switch = [[-1] * N for _ in range(N)]

    # 壁の管理セット
    fixed_walls = set()  # 絶対不変の壁（スイッチ部屋の囲い・ゴール封鎖等）
    movable_walls = set()  # 焼きなましで変更可能な迷路用壁

    # fixed ドア・スイッチの追跡（焼きなましで触らないため）
    fixed_doors_h = set()
    fixed_doors_v = set()
    fixed_switches_set = set()

    # ============================================================
    # place_chain_with_rooms():
    #   K 個のスイッチを「スイッチ部屋」として配置する。
    #   各スイッチ部屋:
    #     - スイッチの隣接通路セルを固定壁で囲む (入口1か所のみ残す)
    #     - 入口に「前段スイッチが開くドア」を設置
    #   ゴール(N-1,N-1)の入口も固定壁+最後のドアで封鎖する。
    # ============================================================
    def place_chain_with_rooms():
        if K == 0:
            return

        # ------ ゴールへの入口を封鎖 ------
        # NOTE: ゴール近傍から通路セルを列挙し、
        #       1か所だけに最後のドアを置き、残りを fixed_wall で塞ぐ。
        goal_neighbors = []
        for di, dj in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            ni, nj = N - 1 + di, N - 1 + dj
            if 0 <= ni < N and 0 <= nj < N and c[ni][nj] == ".":
                goal_neighbors.append((ni, nj, di, dj))

        door_val_goal = 2 * (K - 1) + 1  # グループ(K-1)がONのとき開く
        goal_door_placed = False
        for ni, nj, di, dj in goal_neighbors:
            if not goal_door_placed:
                # この辺にゴールドアを設置
                if di == -1:
                    # 上から下: (ni,nj)→(N-1,N-1) → door_h[ni][nj]
                    door_h[ni][nj] = door_val_goal
                    fixed_doors_h.add((ni, nj))
                elif di == 1:
                    # 下から上: (ni,nj)→(N-1,N-1) → door_h[N-1][N-1]
                    door_h[N - 1][N - 1] = door_val_goal
                    fixed_doors_h.add((N - 1, N - 1))
                elif dj == -1:
                    # 左から右: (ni,nj)→(N-1,N-1) → door_v[ni][nj]
                    door_v[ni][nj] = door_val_goal
                    fixed_doors_v.add((ni, nj))
                else:
                    # 右から左: (ni,nj)→(N-1,N-1) → door_v[N-1][N-1]
                    door_v[N - 1][N - 1] = door_val_goal
                    fixed_doors_v.add((N - 1, N - 1))
                goal_door_placed = True
            else:
                # 残りの入口は fixed_wall で封鎖
                fixed_walls.add((ni, nj))

        # ------ スイッチ部屋の配置 ------
        # TODO: エリア分割の基準 (N//3 等) はパラメータ調整で改善できるかもしれない
        def get_room_candidates(step):
            """step に応じたエリアから、利用可能なセルを返す"""
            if step % 2 == 1:
                # 奇数ステップ: 右上エリア
                cands = [
                    (i, j)
                    for i, j in empty_cells
                    if i < N // 3
                    and j > (2 * N) // 3
                    and (i, j) not in fixed_switches_set
                    and (i, j) not in fixed_walls
                    and (i, j) != (0, 0)
                    and (i, j) != (N - 1, N - 1)
                ]
            else:
                # 偶数ステップ: 左下エリア
                cands = [
                    (i, j)
                    for i, j in empty_cells
                    if i > (2 * N) // 3
                    and j < N // 3
                    and (i, j) not in fixed_switches_set
                    and (i, j) not in fixed_walls
                    and (i, j) != (0, 0)
                    and (i, j) != (N - 1, N - 1)
                ]
            return cands

        for step in range(K - 1, -1, -1):
            pool = get_room_candidates(step)
            if not pool:
                # FIXME: エリアが空の場合、全通路から fallback するが精度が下がる
                pool = [
                    (i, j)
                    for i, j in empty_cells
                    if (i, j) not in fixed_switches_set
                    and (i, j) not in fixed_walls
                    and (i, j) != (0, 0)
                    and (i, j) != (N - 1, N - 1)
                ]
            if not pool:
                continue

            si, sj = pool[0]

            # スイッチ配置
            switch[si][sj] = step
            fixed_switches_set.add((si, sj))

            # 部屋の囲い: スイッチの4近傍通路セルを列挙
            neighbor_cells = []
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = si + di, sj + dj
                if (
                    0 <= ni < N
                    and 0 <= nj < N
                    and c[ni][nj] == "."
                    and (ni, nj) not in fixed_switches_set
                    and (ni, nj) != (0, 0)
                    and (ni, nj) != (N - 1, N - 1)
                ):
                    neighbor_cells.append((ni, nj, di, dj))

            if not neighbor_cells:
                continue

            # 入口: 1か所目を採用、残りを fixed_wall で封鎖
            eni, enj, edi, edj = neighbor_cells[0]
            for ni, nj, di, dj in neighbor_cells[1:]:
                fixed_walls.add((ni, nj))

            # 入口にドアを設置
            # NOTE: step==0 はチェーンの出発点なのでドア不要（スタートから到達可能）
            if step > 0:
                door_val = 2 * (step - 1) + 1  # グループ(step-1)がONのとき開く
                if edi == 1:
                    # スイッチが下、入口が上 → (eni,enj)→(si,sj) = door_h[eni][enj]
                    door_h[eni][enj] = door_val
                    fixed_doors_h.add((eni, enj))
                elif edi == -1:
                    # スイッチが上、入口が下 → (si,sj)→(eni,enj) = door_h[si][sj]
                    door_h[si][sj] = door_val
                    fixed_doors_h.add((si, sj))
                elif edj == 1:
                    # 入口が右 → (si,sj)→(eni,enj) = door_v[si][sj]
                    door_v[si][sj] = door_val
                    fixed_doors_v.add((si, sj))
                else:
                    # 入口が左 → (eni,enj)→(si,sj) = door_v[eni][enj]
                    door_v[eni][enj] = door_val
                    fixed_doors_v.add((eni, enj))

    place_chain_with_rooms()

    best_T = calc_T(N, K, c, fixed_walls, movable_walls, door_h, door_v, switch)

    # 現在のドア数を数える（M 枚上限管理のため）
    door_count = sum(1 for i in range(N) for j in range(N) if door_h[i][j] != -1 or door_v[i][j] != -1)

    # ============================================================
    # 焼きなましループ（山登り）
    #   操作: Add Door / Remove Door / Move Door
    #   NOTE: 問題仕様上、壁変更は出力できないため movable_walls は使わない。
    #         fixed_walls はスイッチ部屋の囲いとして BFS 計算にのみ使用する。
    # TODO: 温度スケジューリングを実装して焼きなましに格上げする（現状は山登り）
    # ============================================================
    while time.time() - start_time < LIMIT:
        op = random.randint(0, 2)  # 0=Add, 1=Remove, 2=Move

        if op == 0:
            # Add Door: ランダムな辺にドアを追加
            if door_count >= M:
                continue
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 2 if d_type == 0 else N - 1)
            j = random.randint(0, N - 1 if d_type == 0 else N - 2)
            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue
            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]
            if old_g != -1:
                continue  # すでにドアあり
            new_g = random.choice([2 * k + 1 for k in range(K)])
            if d_type == 0:
                door_h[i][j] = new_g
            else:
                door_v[i][j] = new_g
            new_T = calc_T(N, K, c, fixed_walls, movable_walls, door_h, door_v, switch)
            if new_T > best_T:
                best_T = new_T
                door_count += 1
            else:
                if d_type == 0:
                    door_h[i][j] = -1
                else:
                    door_v[i][j] = -1

        elif op == 1:
            # Remove Door: ランダムなドアを削除
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 2 if d_type == 0 else N - 1)
            j = random.randint(0, N - 1 if d_type == 0 else N - 2)
            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue
            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]
            if old_g == -1:
                continue  # ドアなし
            if d_type == 0:
                door_h[i][j] = -1
            else:
                door_v[i][j] = -1
            new_T = calc_T(N, K, c, fixed_walls, movable_walls, door_h, door_v, switch)
            if new_T > best_T:
                best_T = new_T
                door_count -= 1
            else:
                if d_type == 0:
                    door_h[i][j] = old_g
                else:
                    door_v[i][j] = old_g

        else:
            # Move Door: 既存ドアを別の辺へ移動
            d_type = random.randint(0, 1)
            i = random.randint(0, N - 2 if d_type == 0 else N - 1)
            j = random.randint(0, N - 1 if d_type == 0 else N - 2)
            if d_type == 0 and (i, j) in fixed_doors_h:
                continue
            if d_type == 1 and (i, j) in fixed_doors_v:
                continue
            old_g = door_h[i][j] if d_type == 0 else door_v[i][j]
            if old_g == -1:
                continue
            # 移動先をランダムに選ぶ
            d2 = random.randint(0, 1)
            i2 = random.randint(0, N - 2 if d2 == 0 else N - 1)
            j2 = random.randint(0, N - 1 if d2 == 0 else N - 2)
            if d2 == 0 and (i2, j2) in fixed_doors_h:
                continue
            if d2 == 1 and (i2, j2) in fixed_doors_v:
                continue
            existing = door_h[i2][j2] if d2 == 0 else door_v[i2][j2]
            if existing != -1:
                continue
            # 移動実行
            if d_type == 0:
                door_h[i][j] = -1
            else:
                door_v[i][j] = -1
            new_g = random.choice([2 * k + 1 for k in range(K)])
            if d2 == 0:
                door_h[i2][j2] = new_g
            else:
                door_v[i2][j2] = new_g
            new_T = calc_T(N, K, c, fixed_walls, movable_walls, door_h, door_v, switch)
            if new_T > best_T:
                best_T = new_T
            else:
                if d_type == 0:
                    door_h[i][j] = old_g
                else:
                    door_v[i][j] = old_g
                if d2 == 0:
                    door_h[i2][j2] = -1
                else:
                    door_v[i2][j2] = -1

    # ============================================================
    # 出力 (問題仕様: ドア数・ドア一覧・スイッチ数・スイッチ一覧のみ)
    # NOTE: マップ変更は出力形式に含まれないため、fixed_walls は BFS 計算のみに使用。
    # ============================================================
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
