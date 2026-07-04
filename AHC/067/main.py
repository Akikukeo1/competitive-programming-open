import sys
import time
import random
import math
from collections import deque

random.seed(42)  # 再現性のための固定シード


def calc_T(N, K, c, door_h, door_v, switch):
    """BFSで (0,0) から (N-1,N-1) への最小行動回数を計算する。

    状態: (スイッチマスク, 行, 列)
    ドアの open 条件: g が奇数(初期閉) → マスク bit が 1 で open
                    g が偶数(初期開) → マスク bit が 0 で open
    """

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

    # 焼きなまし温度パラメータ
    START_TEMP = 10.0
    END_TEMP = 0.01

    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N, M, K = int(input_data[0]), int(input_data[1]), int(input_data[2])
    c = input_data[3 : 3 + N]

    empty_cells = [(i, j) for i in range(N) for j in range(N) if c[i][j] == "."]

    door_h = [[-1] * N for _ in range(N)]
    door_v = [[-1] * N for _ in range(N)]
    switch = [[-1] * N for _ in range(N)]

    # ---- 初期最短経路を計算 ----
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

    # ---- 固定ギミック管理 ----
    fixed_switches = set()
    fixed_doors_h = set()
    fixed_doors_v = set()
    door_count = 0

    rooms = []

    def get_room_details(room):
        cr, cc = room["center"]
        dir = room["entrance_dir"]

        walls = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                is_entrance = False
                if dir == 0 and dr == -1 and dc == 0:
                    is_entrance = True
                if dir == 1 and dr == 0 and dc == 1:
                    is_entrance = True
                if dir == 2 and dr == 1 and dc == 0:
                    is_entrance = True
                if dir == 3 and dr == 0 and dc == -1:
                    is_entrance = True

                if not is_entrance:
                    walls.append((cr + dr, cc + dc))

        door_info = None
        if dir == 0:
            door_info = ("h", cr - 2, cc)
        elif dir == 1:
            door_info = ("v", cr, cc + 1)
        elif dir == 2:
            door_info = ("h", cr + 1, cc)
        elif dir == 3:
            door_info = ("v", cr, cc - 2)

        return walls, door_info

    def rebuild_map(current_rooms):
        nc = [list(row) for row in c]
        ndoor_h = [[-1] * N for _ in range(N)]
        ndoor_v = [[-1] * N for _ in range(N)]
        nswitch = [[-1] * N for _ in range(N)]

        for room in current_rooms:
            walls, door_info = get_room_details(room)
            for wr, wc in walls:
                if 0 <= wr < N and 0 <= wc < N:
                    nc[wr][wc] = "#"

            cr, cc = room["center"]
            nswitch[cr][cc] = room["switch_type"]

            if room["door_type"] != -1 and door_info:
                dtype, dr, dc = door_info
                if 0 <= dr < N and 0 <= dc < N:
                    if dtype == "h":
                        ndoor_h[dr][dc] = room["door_type"]
                    else:
                        ndoor_v[dr][dc] = room["door_type"]

        return nc, ndoor_h, ndoor_v, nswitch

    def place_rooms():
        """初期解として、部屋のチェーンを配置する。"""
        nonlocal door_count, rooms
        if K == 0:
            return

        # 部屋配置ロジック(簡易実装: スイッチ配置位置の周りに部屋)
        # 部屋配置の候補位置を探す
        room_centers = []
        for i in range(1, N - 1):
            for j in range(1, N - 1):
                # 3x3が空いているか
                can_place = True
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if c[i + dr][j + dc] != ".":
                            can_place = False
                            break
                    if not can_place:
                        break
                if can_place:
                    room_centers.append((i, j))
        random.shuffle(room_centers)

        # 部屋配置
        # 確実に配置するために空き候補を探す
        for step in range(K):
            if not room_centers:
                break

            # 3x3を確保できる場所を毎ステップ探す
            found = False
            for _ in range(100):  # 100回探して見つからなければ断念
                cr, cc = random.choice([(i, j) for i in range(1, N - 1) for j in range(1, N - 1)])

                # 既存の部屋と重ならないかチェック
                can_place = True
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        # 既存部屋の中央付近と被っていないか(簡易的にcenterの距離で判定)
                        for room in rooms:
                            if abs(room["center"][0] - (cr + dr)) <= 1 and abs(room["center"][1] - (cc + dc)) <= 1:
                                can_place = False
                                break
                        if not can_place:
                            break
                    if not can_place:
                        break

                if can_place:
                    found = True
                    break

            if not found:
                continue

            # 入口方向はランダム
            dir = random.randint(0, 3)

            door_type = -1
            if step > 0:
                door_type = 2 * (step - 1) + 1
                door_count += 1

            rooms.append({"center": (cr, cc), "entrance_dir": dir, "switch_type": step, "door_type": door_type})

    place_rooms()
    c, door_h, door_v, switch = rebuild_map(rooms)

    # ---- スコア計算ヘルパー ----
    # NOTE: T を最大化しつつドアも多い状態を優先する。
    #       ドア1枚の重みを1とし、T の重みを1000倍にすることで
    #       T が上がれば必ず採用、同 T ならドアが多い方が勝つ。
    def calc_score(T, dc):
        return T * 1000 + dc

    # ---- 初期スコア ----
    init_T = calc_T(N, K, c, door_h, door_v, switch)
    current_score = calc_score(init_T, door_count)
    best_score = current_score

    best_rooms = [r.copy() for r in rooms]

    # ---- 焼きなましループ ----
    if rooms:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= LIMIT:
                break

            progress = elapsed / LIMIT
            temp = START_TEMP * (END_TEMP / START_TEMP) ** progress

            new_rooms = [room.copy() for room in rooms]
            r = random.random()

            if r < 0.25:  # MoveRoom
                idx = random.randrange(len(rooms))
                # 部屋の中心候補を探す
                candidates = []
                for i in range(1, N - 1):
                    for j in range(1, N - 1):
                        # 3x3が空いているか (自分自身を除く)
                        can_place = True
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                # 既存の部屋のセルと重なっていないか(簡易チェック: スイッチ位置が被っていないか)
                                for room in rooms:
                                    if room["center"] == (i + dr, j + dc):
                                        can_place = False
                                        break
                                if not can_place:
                                    break
                            if not can_place:
                                break
                        if can_place:
                            candidates.append((i, j))
                if candidates:
                    new_rooms[idx]["center"] = random.choice(candidates)

            elif r < 0.50:  # RotateRoom
                idx = random.randrange(len(rooms))
                new_rooms[idx]["entrance_dir"] = (new_rooms[idx]["entrance_dir"] + 1) % 4

            elif r < 0.75:  # SwapRoom
                idx1 = random.randrange(len(rooms))
                idx2 = random.randrange(len(rooms))
                new_rooms[idx1], new_rooms[idx2] = new_rooms[idx2], new_rooms[idx1]

            else:  # ChangeDoorType
                idx = random.randrange(len(rooms))
                if new_rooms[idx]["door_type"] != -1:
                    new_rooms[idx]["door_type"] = random.choice([2 * k + 1 for k in range(K)])

            # 盤面再構築
            nc, ndh, ndv, nsw = rebuild_map(new_rooms)

            new_T = calc_T(N, K, nc, ndh, ndv, nsw)

            # 新しいドア数 dc を計算
            ndc = sum(1 for room in new_rooms if room["door_type"] != -1)
            new_score = calc_score(new_T, ndc)

            delta = new_score - current_score

            if delta >= 0 or random.random() < math.exp(delta / temp):
                rooms = new_rooms
                c, door_h, door_v, switch = nc, ndh, ndv, nsw
                current_score = new_score
                if current_score > best_score:
                    best_score = current_score
                    best_rooms = [room.copy() for room in rooms]

    # ---- 出力 (best状態を使う) ----
    # best_rooms を使って最終盤面を生成
    best_c, best_door_h, best_door_v, best_switch = rebuild_map(best_rooms)

    out_doors = []
    for i in range(N):
        for j in range(N):
            if best_door_h[i][j] != -1:
                out_doors.append((0, i, j, best_door_h[i][j]))
            if best_door_v[i][j] != -1:
                out_doors.append((1, i, j, best_door_v[i][j]))
    out_switches = []
    for i in range(N):
        for j in range(N):
            if best_switch[i][j] != -1:
                out_switches.append((i, j, best_switch[i][j]))

    print(len(out_doors))
    for d, i, j, g in out_doors:
        print(f"{d} {i} {j} {g}")
    print(len(out_switches))
    for p, q, s in out_switches:
        print(f"{p} {q} {s}")


if __name__ == "__main__":
    solve()
