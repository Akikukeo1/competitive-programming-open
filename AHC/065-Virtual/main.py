import sys


def main():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    N = 20
    ptr = 1

    grid = []
    for _ in range(N):
        grid.append(list(map(int, input_data[ptr : ptr + N])))
        ptr += N

    # --- 1. ベルトコンベアの設計 (M = 11) ---
    conveyors = []

    # 0〜9番目のコンベア: 2行ずつをペアにして、グリッドを横に正しく1周するループ (長さ40)
    # 例: 0行目を左から右(0->19)へ行き、1行目を右から左(19->0)へ戻る
    for i in range(10):
        r1 = i * 2
        r2 = i * 2 + 1
        loop = []
        for c in range(N):
            loop.append((r1, c))
        for c in range(N - 1, -1, -1):
            loop.append((r2, c))
        conveyors.append(loop)

    # 10番目のコンベア: 10列目と11列目をペアにして、縦に正しく1周するループ (長さ40)
    # 10列目を上から下(0->19)へ下り、11列目を下から上(19->0)へ上る
    EXIT_COL = 10
    NEXT_COL = 11
    col_loop = []
    for r in range(N):
        col_loop.append((r, EXIT_COL))
    for r in range(N - 1, -1, -1):
        col_loop.append((r, NEXT_COL))
    conveyors.append(col_loop)

    # 各コンベアのマスの位置を特定するための辞書
    # conv_maps[m] = {(r, c): index_in_loop}
    conv_maps = []
    for conv in conveyors:
        conv_maps.append({pos: idx for idx, pos in enumerate(conv)})

    commands = []
    target = 0
    MAX_T = 100000

    # シミュレーション用のヘルパー関数（コンベアを実際に回転させる）
    def rotate_conveyor(m, direction, steps):
        nonlocal commands
        for _ in range(steps):
            if len(commands) >= MAX_T:
                break
            commands.append((m, direction))

            # コンベア上の現在の値を取り出す
            conv_cells = conveyors[m]
            vals = [grid[r][c] for r, c in conv_cells]

            # 回転処理
            if direction == 1:
                # 時計回り: 末尾が先頭に来る
                vals = [vals[-1]] + vals[:-1]
            else:
                # 反時計回り: 先頭が末尾に行く
                vals = vals[1:] + [vals[0]]

            # グリッドに書き戻す
            for idx, (r, c) in enumerate(conv_cells):
                grid[r][c] = vals[idx]

    # 最初から搬出口に target (0) がある場合の自動搬出チェック
    while target < N * N and grid[0][EXIT_COL] == target:
        grid[0][EXIT_COL] = -1
        target += 1

    # 400個すべての箱を搬出するまでループ
    while target < N * N and len(commands) < MAX_T:
        # 1. 現在の target の位置 (curr_r, curr_c) を探す
        curr_r, curr_c = -1, -1
        for r in range(N):
            for c in range(N):
                if grid[r][c] == target:
                    curr_r, curr_c = r, c
                    break
            if curr_r != -1:
                break

        if curr_r == -1:
            target += 1
            continue

        # 2. 搬出口 (0, 10) に既にあるなら搬出
        if curr_r == 0 and curr_c == EXIT_COL:
            grid[0][EXIT_COL] = -1
            target += 1
            while target < N * N and grid[0][EXIT_COL] == target:
                grid[0][EXIT_COL] = -1
                target += 1
            continue

        # Step A: 箱を「10列目」または「11列目」のいずれかに移動させる (横コンベアの操作)
        if curr_c != EXIT_COL and curr_c != NEXT_COL:
            m_idx = curr_r // 2  # 対応する横コンベアの番号

            # 現在のループ内インデックス
            p_start = conv_maps[m_idx][(curr_r, curr_c)]
            # 目標位置：同じ行の EXIT_COL (10) の位置
            p_goal = conv_maps[m_idx][(curr_r, EXIT_COL)]

            L = len(conveyors[m_idx])
            cw_steps = (p_goal - p_start) % L
            ccw_steps = (p_start - p_goal) % L

            if cw_steps <= ccw_steps:
                rotate_conveyor(m_idx, 1, cw_steps)
            else:
                rotate_conveyor(m_idx, -1, ccw_steps)

            # 位置を更新
            curr_c = EXIT_COL

        # Step B: 箱を 縦コンベア(m=10) を使って 搬出口 (0, 10) に移動させる
        # この時点で箱は必ず 10列目か11列目のどこかにいます
        m_idx = 10  # 縦コンベア
        p_start = conv_maps[m_idx][(curr_r, curr_c)]
        p_goal = conv_maps[m_idx][(0, EXIT_COL)]  # 搬出口 (0, 10)

        L = len(conveyors[m_idx])
        cw_steps = (p_goal - p_start) % L
        ccw_steps = (p_start - p_goal) % L

        if cw_steps <= ccw_steps:
            rotate_conveyor(m_idx, 1, cw_steps)
        else:
            rotate_conveyor(m_idx, -1, ccw_steps)

        # 3. 移動後、搬出口 (0, 10) に到着したはずなので搬出する
        if grid[0][EXIT_COL] == target:
            grid[0][EXIT_COL] = -1
            target += 1
            # 連鎖搬出チェック
            while target < N * N and grid[0][EXIT_COL] == target:
                grid[0][EXIT_COL] = -1
                target += 1

    # --- 出力パート ---
    M = len(conveyors)
    print(M)
    for loop in conveyors:
        print(f"{len(loop)} " + " ".join(f"{r} {c}" for r, c in loop))

    print(len(commands))
    for m, d in commands:
        print(f"{m} {d}")


if __name__ == "__main__":
    main()
