#include <bits/stdc++.h>
using namespace std;

int N, M, K;
vector<string> grid;
vector<vector<bool>> fixed_wall;
vector<vector<int>> door_h, door_v, switches;
vector<pair<int,int>> empty_cells;
set<pair<int,int>> fixed_switches;

int calc_T_with_grid() {
    auto is_open = [](int g, int mask) -> bool {
        if (g == -1) return true;
        return ((mask >> (g / 2)) & 1) == (g & 1);
    };

    const int S = 1 << K;
    vector<int> dist(S * N * N, -1);
    auto idx = [&](int mask, int i, int j) { return (mask * N + i) * N + j; };
    dist[idx(0, 0, 0)] = 0;

    struct State { int mask, i, j; };
    deque<State> que;
    que.push_back({0, 0, 0});

    const int di[4] = {-1, 1, 0, 0};
    const int dj[4] = {0, 0, -1, 1};

    while (!que.empty()) {
        auto [mask, i, j] = que.front(); que.pop_front();
        int d = dist[idx(mask, i, j)];

        if (i == N - 1 && j == N - 1) return d;

        for (int dir = 0; dir < 4; dir++) {
            int ni = i + di[dir], nj = j + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N) continue;
            if (grid[ni][nj] == '#') continue;

            int g;
            if (di[dir] == 1) g = door_h[i][j];
            else if (di[dir] == -1) g = door_h[ni][nj];
            else if (dj[dir] == 1) g = door_v[i][j];
            else g = door_v[ni][nj];

            if (!is_open(g, mask)) continue;

            int nidx = idx(mask, ni, nj);
            if (dist[nidx] == -1) {
                dist[nidx] = d + 1;
                que.push_back({mask, ni, nj});
            }
        }

        int s = switches[i][j];
        if (s != -1) {
            int nmask = mask ^ (1 << s);
            int nidx = idx(nmask, i, j);
            if (dist[nidx] == -1) {
                dist[nidx] = d + 1;
                que.push_back({nmask, i, j});
            }
        }
    }
    return 0;
}

void place_chain(int &door_count) {
    if (K == 0) return;

    int cx = N / 2, cy = N / 2;

    // Goal room
    int gi = N - 1, gj = N - 1;
    int goal_edi = 0, goal_edj = 0;
    bool has_goal_entrance = false;
    int goal_dirs[2][2] = {{-1, 0}, {0, -1}};
    for (auto &d : goal_dirs) {
        int ni = gi + d[0], nj = gj + d[1];
        if (ni >= 0 && ni < N && nj >= 0 && nj < N && grid[ni][nj] == '.') {
            goal_edi = d[0]; goal_edj = d[1];
            has_goal_entrance = true;
            break;
        }
    }
    if (has_goal_entrance) {
        int block_dirs[2][2] = {{-1, 0}, {0, -1}};
        for (auto &bd : block_dirs) {
            if (bd[0] == goal_edi && bd[1] == goal_edj) continue;
            int bi = gi + bd[0], bj = gj + bd[1];
            if (bi >= 0 && bi < N && bj >= 0 && bj < N && grid[bi][bj] == '.' && !(bi == 0 && bj == 0)) {
                grid[bi][bj] = '#';
                fixed_wall[bi][bj] = true;
            }
        }
        int ni = gi + goal_edi, nj = gj + goal_edj;
        if (goal_edi == -1) {
            door_h[ni][nj] = 2 * (K - 1) + 1;
        } else {
            door_v[ni][nj] = 2 * (K - 1) + 1;
        }
        door_count++;
    }

    // Switch rooms
    vector<pair<int,int>> tr_cells, bl_cells;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (grid[i][j] == '.' && !(i == 0 && j == 0) && !(i == N-1 && j == N-1)) {
                if (i < N / 3 && j > (2 * N) / 3) tr_cells.emplace_back(i, j);
                if (i > (2 * N) / 3 && j < N / 3) bl_cells.emplace_back(i, j);
            }
        }
    }

    for (int step = K - 1; step >= 0; step--) {
        vector<pair<int,int>> *pool = (step % 2 == 1) ? &tr_cells : &bl_cells;
        if (pool->empty()) {
            for (auto &cell : empty_cells) {
                if (fixed_switches.count(cell)) continue;
                if (cell.first == 0 && cell.second == 0) continue;
                if (cell.first == N - 1 && cell.second == N - 1) continue;
                pool->push_back(cell);
            }
        }
        if (pool->empty()) continue;

        auto [si, sj] = pool->front();
        pool->erase(pool->begin());
        switches[si][sj] = step;
        fixed_switches.emplace(si, sj);

        // Determine entrance direction
        vector<pair<int,int>> preferred;
        if (si > cx) preferred.emplace_back(-1, 0);
        else if (si < cx) preferred.emplace_back(1, 0);
        if (sj > cy) preferred.emplace_back(0, -1);
        else if (sj < cy) preferred.emplace_back(0, 1);
        const int all_dirs[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
        for (auto &d : all_dirs) {
            bool found = false;
            for (auto &p : preferred) {
                if (p.first == d[0] && p.second == d[1]) { found = true; break; }
            }
            if (!found) preferred.emplace_back(d[0], d[1]);
        }

        int ent_di = 0, ent_dj = 0;
        bool has_entrance = false;
        for (auto &d : preferred) {
            int ni = si + d.first, nj = sj + d.second;
            if (ni >= 0 && ni < N && nj >= 0 && nj < N && grid[ni][nj] == '.' && !(ni == 0 && nj == 0)) {
                ent_di = d.first; ent_dj = d.second;
                has_entrance = true;
                break;
            }
        }
        if (!has_entrance) continue;

        // Room walls on 3 sides
        for (auto &d : all_dirs) {
            if (d[0] == ent_di && d[1] == ent_dj) continue;
            int ni = si + d[0], nj = sj + d[1];
            if (ni >= 0 && ni < N && nj >= 0 && nj < N && !(ni == 0 && nj == 0)) {
                if (grid[ni][nj] == '.') {
                    grid[ni][nj] = '#';
                    fixed_wall[ni][nj] = true;
                }
            }
        }

        // Door at entrance
        if (step > 0) {
            int ni = si + ent_di, nj = sj + ent_dj;
            int door_val = 2 * (step - 1) + 1;
            if (ent_di != 0) {
                if (ent_di == 1) door_h[si][sj] = door_val;
                else door_h[ni][nj] = door_val;
            } else {
                if (ent_dj == 1) door_v[si][sj] = door_val;
                else door_v[ni][nj] = door_val;
            }
            door_count++;
        }
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    auto start_time = chrono::steady_clock::now();
    const double LIMIT = 1.95;

    cin >> N >> M >> K;
    grid.resize(N);
    for (int i = 0; i < N; i++) cin >> grid[i];

    fixed_wall.assign(N, vector<bool>(N, false));
    door_h.assign(N, vector<int>(N, -1));
    door_v.assign(N, vector<int>(N, -1));
    switches.assign(N, vector<int>(N, -1));

    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            if (grid[i][j] == '.')
                empty_cells.emplace_back(i, j);

    int door_count = 0;
    place_chain(door_count);

    int best_T = calc_T_with_grid();
    vector<string> best_grid = grid;

    random_device rd;
    mt19937_64 rng(rd());

    // SA loop
    while (true) {
        auto now = chrono::steady_clock::now();
        double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();
        if (elapsed >= LIMIT) break;

        vector<pair<int,int>> movable_empty, movable_walls;
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                if (fixed_wall[i][j]) continue;
                if (i == 0 && j == 0) continue;
                if (i == N - 1 && j == N - 1) continue;
                if (grid[i][j] == '#') movable_walls.emplace_back(i, j);
                else movable_empty.emplace_back(i, j);
            }
        }

        if (movable_walls.empty() && movable_empty.empty()) break;

        double op = (double)(rng() & 0x7FFFFFFF) / 0x7FFFFFFF;
        // or use uniform_real_distribution
        // simpler: op = uniform_real_distribution<>(0,1)(rng)

        if (op < 0.3 && !movable_walls.empty()) {
            auto [i, j] = movable_walls[rng() % movable_walls.size()];
            grid[i][j] = '.';
            int new_T = calc_T_with_grid();
            if (new_T > best_T) {
                best_T = new_T;
                best_grid = grid;
            } else {
                grid[i][j] = '#';
            }
        } else if (op < 0.6 && !movable_empty.empty()) {
            auto [i, j] = movable_empty[rng() % movable_empty.size()];
            grid[i][j] = '#';
            int new_T = calc_T_with_grid();
            if (new_T > best_T) {
                best_T = new_T;
                best_grid = grid;
            } else {
                grid[i][j] = '.';
            }
        } else if (!movable_walls.empty() && !movable_empty.empty()) {
            auto [ri, rj] = movable_walls[rng() % movable_walls.size()];
            auto [ai, aj] = movable_empty[rng() % movable_empty.size()];
            char old_r = grid[ri][rj], old_a = grid[ai][aj];
            grid[ri][rj] = '.';
            grid[ai][aj] = '#';
            int new_T = calc_T_with_grid();
            if (new_T > best_T) {
                best_T = new_T;
                best_grid = grid;
            } else {
                grid[ri][rj] = old_r;
                grid[ai][aj] = old_a;
            }
        } else if (!movable_empty.empty()) {
            auto [i, j] = movable_empty[rng() % movable_empty.size()];
            grid[i][j] = '#';
            int new_T = calc_T_with_grid();
            if (new_T > best_T) {
                best_T = new_T;
                best_grid = grid;
            } else {
                grid[i][j] = '.';
            }
        } else if (!movable_walls.empty()) {
            auto [i, j] = movable_walls[rng() % movable_walls.size()];
            grid[i][j] = '.';
            int new_T = calc_T_with_grid();
            if (new_T > best_T) {
                best_T = new_T;
                best_grid = grid;
            } else {
                grid[i][j] = '#';
            }
        }
    }

    // Output
    vector<tuple<int,int,int,int>> out_doors;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (door_h[i][j] != -1) out_doors.emplace_back(0, i, j, door_h[i][j]);
            if (door_v[i][j] != -1) out_doors.emplace_back(1, i, j, door_v[i][j]);
        }
    }
    vector<tuple<int,int,int>> out_switches;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (switches[i][j] != -1) out_switches.emplace_back(i, j, switches[i][j]);
        }
    }

    cout << out_doors.size() << "\n";
    for (auto &[d, i, j, g] : out_doors) cout << d << " " << i << " " << j << " " << g << "\n";
    cout << out_switches.size() << "\n";
    for (auto &[p, q, s] : out_switches) cout << p << " " << q << " " << s << "\n";

    return 0;
}
