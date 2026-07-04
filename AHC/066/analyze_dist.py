import sys


def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    it = iter(input_data)
    n = int(next(it))
    m = int(next(it))
    t = int(next(it))
    v_walls = [next(it) for _ in range(n)]
    h_walls = [next(it) for _ in range(n - 1)]
    balls = []
    baskets = []
    for _ in range(m):
        r1, c1, r2, c2 = int(next(it)), int(next(it)), int(next(it)), int(next(it))
        balls.append((r1, c1))
        baskets.append((r2, c2))

    def get_dist(r1, c1, r2, c2):
        dist = [[-1] * n for _ in range(n)]
        dist[r1][c1] = 0
        q = [(r1, c1)]
        idx = 0
        while idx < len(q):
            r, c = q[idx]
            idx += 1
            if r == r2 and c == c2:
                return dist[r][c]
            # UP
            if r > 0 and h_walls[r - 1][c] == "0" and dist[r - 1][c] == -1:
                dist[r - 1][c] = dist[r][c] + 1
                q.append((r - 1, c))
            # DOWN
            if r < n - 1 and h_walls[r][c] == "0" and dist[r + 1][c] == -1:
                dist[r + 1][c] = dist[r][c] + 1
                q.append((r + 1, c))
            # LEFT
            if c > 0 and v_walls[r][c - 1] == "0" and dist[r][c - 1] == -1:
                dist[r][c - 1] = dist[r][c] + 1
                q.append((r, c - 1))
            # RIGHT
            if c < n - 1 and v_walls[r][c] == "0" and dist[r][c + 1] == -1:
                dist[r][c + 1] = dist[r][c] + 1
                q.append((r, c + 1))
        return 1000

    # Precompute all-pairs shortest paths between balls, baskets, and start
    nodes = [(0, 0)] + balls + baskets
    num_nodes = len(nodes)
    dist_matrix = [[0] * num_nodes for _ in range(num_nodes)]
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            d = get_dist(nodes[i][0], nodes[i][1], nodes[j][0], nodes[j][1])
            dist_matrix[i][j] = dist_matrix[j][i] = d

    total_fixed_dist = 0
    for i in range(m):
        total_fixed_dist += dist_matrix[1 + i][1 + m + i]
    print(f"Total fixed distance (P_i -> D_i): {total_fixed_dist}")

    # TSP distance
    # Job i is picking up ball i (index 1+i) and delivering to basket i (index 1+m+i)
    # Total distance = dist(curr, P_i) + dist(P_i, D_i)
    # We only optimize the order of jobs.

    # job_dist[i][j] is the distance from job i's delivery to job j's pickup
    job_pickup = [1 + i for i in range(m)]
    job_delivery = [1 + m + i for i in range(m)]

    perm = list(range(m))
    # Greedy initialization
    curr = 0  # start node index
    greedy_perm = []
    visited = [False] * m
    for _ in range(m):
        best_d = 1000
        best_idx = -1
        for i in range(m):
            if not visited[i]:
                d = dist_matrix[curr][job_pickup[i]]
                if d < best_d:
                    best_d = d
                    best_idx = i
        greedy_perm.append(best_idx)
        visited[best_idx] = True
        curr = job_delivery[best_idx]

    def calc_score(p):
        d = dist_matrix[0][job_pickup[p[0]]]
        for i in range(m - 1):
            d += dist_matrix[job_delivery[p[i]]][job_pickup[p[i + 1]]]
        return d

    best_p = greedy_perm
    best_score = calc_score(best_p)

    # 2-opt
    improved = True
    while improved:
        improved = False
        for i in range(m):
            for j in range(i + 1, m):
                new_p = best_p[:i] + best_p[i : j + 1][::-1] + best_p[j + 1 :]
                new_score = calc_score(new_p)
                if new_score < best_score:
                    best_score = new_score
                    best_p = new_p
                    improved = True

    print(f"Total TSP distance (2-opt): {best_score}")
    print(f"Total base actions (excluding S): {total_fixed_dist + best_score}")
    print(f"Total base actions (including 2M S): {total_fixed_dist + best_score + 2 * m}")
    print(f"Best permutation: {best_p}")

    # Check for chained swap possibilities
    savings = 0
    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            # Regular: P_i -> D_i, then D_i -> P_j, then P_j -> D_j
            # Cost = dist(P_i, D_i) + dist(D_i, P_j) + dist(P_j, D_j)
            # Chained: P_i -> P_j (Swap), then P_j -> D_j (Swap), then D_j -> D_i (Swap)
            # Cost = dist(P_i, P_j) + dist(P_j, D_j) + dist(D_j, D_i)
            # Note: 3 Swaps instead of 4, but let's compare distance first
            reg_d = dist_matrix[job_pickup[i]][job_delivery[i]] + dist_matrix[job_delivery[i]][job_pickup[j]]
            chain_d = dist_matrix[job_pickup[i]][job_pickup[j]] + dist_matrix[job_delivery[j]][job_delivery[i]]
            if chain_d < reg_d:
                print(f"Chained Swap potential: Ball {i} and {j}, Saving: {reg_d - chain_d}")


solve()
