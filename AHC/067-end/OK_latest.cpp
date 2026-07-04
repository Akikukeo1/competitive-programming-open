#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <sys/time.h>
#include <cstdint>
#include <cstring>

using namespace std;

struct Door { int d, i, j, g; };
struct Switch { int i, j, s; };
struct State { int m, i, j; };
struct Config {
    long long W; vector<Door> doors; vector<Switch> switches;
    bool operator<(const Config& o) const { return W > o.W; }
};

int N = 20, M = 50, K = 10;
string grid[20];
int di[] = {-1, 1, 0, 0};
int dj[] = {0, 0, -1, 1};

int door_h[20][20], door_v[20][20], switch_map[20][20];
int dist_arr[1024][20][20];
State history_q[409600], que[409600];

inline double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

// 高速乱数生成器
inline uint32_t xor_shift() {
    static uint32_t y = 2463534242;
    y ^= (y << 13);
    y ^= (y >> 17);
    return y ^= (y << 5);
}

// 実際の行動回数を計算する高速BFS
long long calc_T(const vector<Door>& doors, const vector<Switch>& switches) {
    for (const auto& d : doors) {
        if (d.d == 0) door_h[d.i][d.j] = d.g; else door_v[d.i][d.j] = d.g;
    }
    for (const auto& s : switches) switch_map[s.i][s.j] = s.s;

    int head = 0, tail = 0, hist_cnt = 0;
    que[tail++] = {0, 0, 0};
    dist_arr[0][0][0] = 0;
    history_q[hist_cnt++] = {0, 0, 0};

    long long ans = 0;
    while (head < tail) {
        auto u = que[head++];
        int d = dist_arr[u.m][u.i][u.j];
        if (u.i == N - 1 && u.j == N - 1) { ans = d; break; }

        for (int dir = 0; dir < 4; ++dir) {
            int ni = u.i + di[dir], nj = u.j + dj[dir];
            if (ni < 0 || ni >= N || nj < 0 || nj >= N || grid[ni][nj] == '#') continue;

            int g = -1;
            if (dir == 1) g = door_h[u.i][u.j]; else if (dir == 0) g = door_h[ni][nj];
            else if (dir == 3) g = door_v[u.i][u.j]; else if (dir == 2) g = door_v[ni][nj];

            if (g != -1 && (((u.m >> (g >> 1)) & 1) != (g & 1))) continue;

            if (dist_arr[u.m][ni][nj] == -1) {
                dist_arr[u.m][ni][nj] = d + 1;
                que[tail++] = {u.m, ni, nj};
                history_q[hist_cnt++] = {u.m, ni, nj};
            }
        }
        int s = switch_map[u.i][u.j];
        if (s != -1) {
            int nmask = u.m ^ (1 << s);
            if (dist_arr[nmask][u.i][u.j] == -1) {
                dist_arr[nmask][u.i][u.j] = d + 1;
                que[tail++] = {nmask, u.i, u.j};
                history_q[hist_cnt++] = {nmask, u.i, u.j};
            }
        }
    }
    for (int i = 0; i < hist_cnt; ++i) dist_arr[history_q[i].m][history_q[i].i][history_q[i].j] = -1;
    for (const auto& d : doors) { if (d.d == 0) door_h[d.i][d.j] = -1; else door_v[d.i][d.j] = -1; }
    for (const auto& s : switches) switch_map[s.i][s.j] = -1;
    return ans;
}

Door make_door(int u, int v, int g) {
    int r1 = u / 20, c1 = u % 20, r2 = v / 20, c2 = v % 20;
    return (r1 == r2) ? Door{1, r1, min(c1, c2), g} : Door{0, min(r1, r2), c1, g};
}

int grid_head[400], grid_to[1600], grid_nxt[1600], grid_edge_cnt;
int tree_head[400], tree_to[800], tree_nxt[800], tree_edge_cnt;
bool vis[400];
int parent_tree[400], depth[400], max_d[400], best_leaf[400];
bool cut_e[400][400];
int comp[400];

vector<Config> top_configs;

// 山登り用にグローバル化
bool is_tree_edge[400][400] = {false};
struct Edge { int u, v; };
Edge all_edges[800];
int all_edges_cnt = 0;

int bfs_order[400];
int bfs_tail = 0;

long long best_S0_val[400];
int best_S0_node[400];
long long dp_arr[10][400];
int parent_dp[10][400];

// 現在のis_tree_edgeからBFSを回して木情報を再構築する
void build_tree_bfs() {
    tree_edge_cnt = 0;
    memset(tree_head, -1, sizeof(tree_head));
    for(int e = 0; e < all_edges_cnt; ++e) {
        int u = all_edges[e].u, v = all_edges[e].v;
        if(is_tree_edge[u][v]) {
            tree_to[tree_edge_cnt] = v; tree_nxt[tree_edge_cnt] = tree_head[u]; tree_head[u] = tree_edge_cnt++;
            tree_to[tree_edge_cnt] = u; tree_nxt[tree_edge_cnt] = tree_head[v]; tree_head[v] = tree_edge_cnt++;
        }
    }

    int q_head = 0; bfs_tail = 0;
    bfs_order[bfs_tail++] = 0;
    parent_tree[0] = -1;
    depth[0] = 0;
    while(q_head < bfs_tail) {
        int u = bfs_order[q_head++];
        for(int e = tree_head[u]; e != -1; e = tree_nxt[e]) {
            int v = tree_to[e];
            if(v != parent_tree[u]) {
                parent_tree[v] = u; depth[v] = depth[u] + 1; bfs_order[bfs_tail++] = v;
            }
        }
    }
}

// 構築された木に対してDP評価およびConfig（状態）の保存を行う
long long evaluate_tree_dp(bool generate_config) {
    int P[400], p_sz = 0;
    int curr = 399;
    while (curr != -1 && curr != 0) { P[p_sz++] = curr; curr = parent_tree[curr]; }
    if (curr == -1) return -1e18; // 399から0に到達できない場合は破棄
    P[p_sz++] = 0;

    for(int i = 0; i < p_sz / 2; ++i) swap(P[i], P[p_sz - 1 - i]);
    if (p_sz < 12) return -1e18;

    for(int i = bfs_tail - 1; i >= 0; --i) {
        int u = bfs_order[i];
        max_d[u] = 0; best_leaf[u] = u;
        for(int e = tree_head[u]; e != -1; e = tree_nxt[e]) {
            int v = tree_to[e];
            if(v != parent_tree[u]) {
                if(max_d[v] + 1 > max_d[u]) {
                    max_d[u] = max_d[v] + 1; best_leaf[u] = best_leaf[v];
                }
            }
        }
    }

    int L_branch[400], F_branch[400], S_branch[400];
    for(int i = 0; i < p_sz; ++i) L_branch[i] = -1;
    int cands[400], C = 0;
    for(int i = 0; i < p_sz - 2; ++i) {
        int u = P[i], nxt_P = P[i + 1];
        int b_max = -1, b_F = -1, b_S = -1;
        for(int e = tree_head[u]; e != -1; e = tree_nxt[e]) {
            int v = tree_to[e];
            if(v != parent_tree[u] && v != nxt_P) {
                if(max_d[v] + 1 > b_max) { b_max = max_d[v] + 1; b_F = v; b_S = best_leaf[v]; }
            }
        }
        if(b_max >= 1) {
            L_branch[i] = b_max; F_branch[i] = b_F; S_branch[i] = b_S;
            if(i >= 1) cands[C++] = i;
        }
    }
    if(C < 9) return -1e18;

    long long cur_max = 0;
    int cur_node = P[0];
    for(int i = 0; i < p_sz; ++i) {
        best_S0_val[i] = cur_max; best_S0_node[i] = cur_node;
        if(L_branch[i] >= 0) {
            long long val = 1024LL * L_branch[i] - 1022LL * i;
            if(val > cur_max) { cur_max = val; cur_node = S_branch[i]; }
        }
    }

    for(int ci = 0; ci < C; ++ci) {
        int c1 = cands[ci];
        dp_arr[1][ci] = (best_S0_val[c1] > -1e17) ? best_S0_val[c1] + 512LL * c1 + 512LL * L_branch[c1] : -1e18;
    }

    for(int k = 2; k <= 9; ++k) {
        long long max_prev = -1e18; int best_prev_ci = -1;
        for(int ci = 0; ci < C; ++ci) {
            int ck = cands[ci];
            if(max_prev > -1e17) {
                dp_arr[k][ci] = max_prev + (1LL << (10 - k)) * ck + (1LL << (10 - k)) * L_branch[ck];
                parent_dp[k][ci] = best_prev_ci;
            } else {
                dp_arr[k][ci] = -1e18;
            }
            if(dp_arr[k - 1][ci] > max_prev) { max_prev = dp_arr[k - 1][ci]; best_prev_ci = ci; }
        }
    }

    long long max_dp = -1e18; int best_last_ci = -1;
    for(int ci = 0; ci < C; ++ci) if(dp_arr[9][ci] > max_dp) { max_dp = dp_arr[9][ci]; best_last_ci = ci; }
    if(max_dp < 0) return -1e18;

    int opt_ci[10], curr_ci = best_last_ci;
    for(int k = 9; k >= 1; --k) { opt_ci[k] = curr_ci; curr_ci = parent_dp[k][curr_ci]; }

    int idxs[10];
    for(int k = 1; k <= 9; ++k) idxs[k] = cands[opt_ci[k]];

    for(int k = 1; k <= 9; ++k) {
        cut_e[P[idxs[k]]][P[idxs[k] + 1]] = cut_e[P[idxs[k] + 1]][P[idxs[k]]] = true;
        cut_e[P[idxs[k]]][F_branch[idxs[k]]] = cut_e[F_branch[idxs[k]]][P[idxs[k]]] = true;
    }
    int u_end = P[p_sz - 2], v_end = P[p_sz - 1];
    cut_e[u_end][v_end] = cut_e[v_end][u_end] = true;

    memset(comp, -1, sizeof(comp));
    int c_id = 0;
    for(int i = 0; i < bfs_tail; ++i) {
        int u_bfs = bfs_order[i];
        if(comp[u_bfs] != -1) continue;
        int cq[400], cq_head = 0, cq_tail = 0;
        cq[cq_tail++] = u_bfs; comp[u_bfs] = c_id;
        while(cq_head < cq_tail) {
            int u = cq[cq_head++];
            for(int e = tree_head[u]; e != -1; e = tree_nxt[e]) {
                int v = tree_to[e];
                if(comp[v] == -1 && !cut_e[u][v]) { comp[v] = c_id; cq[cq_tail++] = v; }
            }
        }
        c_id++;
    }

    int cross_count = 0;
    for(int e = 0; e < all_edges_cnt; ++e) {
        int u = all_edges[e].u, v = all_edges[e].v;
        if(comp[u] != comp[v]) cross_count++;
    }

    long long final_W = -1e18;
    if(cross_count <= 50) {
        final_W = max_dp + 2LL * (p_sz - 2);

        if (generate_config) {
            Config config;
            config.W = final_W;
            for (int k = 1; k <= 9; ++k) {
                config.doors.push_back(make_door(P[idxs[k]], P[idxs[k] + 1], 2 * k - 2));
                config.doors.push_back(make_door(P[idxs[k]], F_branch[idxs[k]], 2 * k - 1));
            }
            config.doors.push_back(make_door(u_end, v_end, 19));

            int added_doors = 19;
            for(int e = 0; e < all_edges_cnt; ++e) {
                int u = all_edges[e].u, v = all_edges[e].v;
                if (comp[u] != comp[v] && !cut_e[u][v]) {
                    config.doors.push_back(make_door(u, v, (u == v_end || v == v_end) ? 17 : 19));
                    added_doors++;
                }
            }

            int int_edges[800], int_cnt = 0;
            for(int e = 0; e < all_edges_cnt; ++e) {
                int u = all_edges[e].u, v = all_edges[e].v;
                if (comp[u] == comp[v] && !is_tree_edge[u][v]) int_edges[int_cnt++] = e;
            }
            sort(int_edges, int_edges + int_cnt, [&](int e1, int e2) {
                int u1 = all_edges[e1].u, v1 = all_edges[e1].v;
                int u2 = all_edges[e2].u, v2 = all_edges[e2].v;
                return abs(depth[u1] - depth[v1]) > abs(depth[u2] - depth[v2]);
            });
            for(int i = 0; i < int_cnt && added_doors < 50; ++i) {
                int e = int_edges[i], u = all_edges[e].u, v = all_edges[e].v;
                config.doors.push_back(make_door(u, v, (u == v_end || v == v_end) ? 17 : 19));
                added_doors++;
            }

            for (int k = 1; k <= 9; ++k) config.switches.push_back({S_branch[idxs[k]] / 20, S_branch[idxs[k]] % 20, k});
            int s0 = best_S0_node[idxs[1]];
            config.switches.push_back({s0 / 20, s0 % 20, 0});

            // 保持サイズを100件に拡張してcalc_Tでの再評価チャンスを増やす
            if (top_configs.size() < 100 || config.W > top_configs.back().W) {
                top_configs.push_back(config);
                sort(top_configs.begin(), top_configs.end());
                if (top_configs.size() > 100) top_configs.pop_back();
            }
        }
    }

    for(int k = 1; k <= 9; ++k) {
        cut_e[P[idxs[k]]][P[idxs[k] + 1]] = cut_e[P[idxs[k] + 1]][P[idxs[k]]] = false;
        cut_e[P[idxs[k]]][F_branch[idxs[k]]] = cut_e[F_branch[idxs[k]]][P[idxs[k]]] = false;
    }
    cut_e[u_end][v_end] = cut_e[v_end][u_end] = false;

    return final_W;
}

int main() {
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    if (!(cin >> N >> M >> K)) return 0;
    for (int i = 0; i < N; ++i) cin >> grid[i];

    memset(dist_arr, -1, sizeof(dist_arr));
    memset(door_h, -1, sizeof(door_h)); memset(door_v, -1, sizeof(door_v)); memset(switch_map, -1, sizeof(switch_map));
    memset(grid_head, -1, sizeof(grid_head));
    grid_edge_cnt = 0;

    for(int r = 0; r < N; ++r) for(int c = 0; c < N; ++c) {
        if(grid[r][c] == '#') continue;
        int u = r * 20 + c;
        if(r + 1 < N && grid[r + 1][c] == '.') {
            int v = (r + 1) * 20 + c;
            grid_to[grid_edge_cnt] = v; grid_nxt[grid_edge_cnt] = grid_head[u]; grid_head[u] = grid_edge_cnt++;
            grid_to[grid_edge_cnt] = u; grid_nxt[grid_edge_cnt] = grid_head[v]; grid_head[v] = grid_edge_cnt++;
        }
        if(c + 1 < N && grid[r][c + 1] == '.') {
            int v = r * 20 + c + 1;
            grid_to[grid_edge_cnt] = v; grid_nxt[grid_edge_cnt] = grid_head[u]; grid_head[u] = grid_edge_cnt++;
            grid_to[grid_edge_cnt] = u; grid_nxt[grid_edge_cnt] = grid_head[v]; grid_head[v] = grid_edge_cnt++;
        }
    }

    // 0から到達可能なマスのみall_edgesに追加（非連結部分によるバグ防止）
    bool reachable[400] = {false};
    int r_q[400], r_head = 0, r_tail = 0;
    r_q[r_tail++] = 0; reachable[0] = true;
    while(r_head < r_tail) {
        int u = r_q[r_head++];
        for(int e = grid_head[u]; e != -1; e = grid_nxt[e]) {
            int v = grid_to[e];
            if(!reachable[v]) { reachable[v] = true; r_q[r_tail++] = v; }
        }
    }

    all_edges_cnt = 0;
    for(int e = 0; e < grid_edge_cnt; e += 2) {
        int u = grid_to[e+1], v = grid_to[e];
        if(reachable[u] && reachable[v]) {
            all_edges[all_edges_cnt++] = {u, v};
        }
    }

    double start_time = get_time();
    int stack_nodes[400];
    int loop_cnt = 0;

    while (true) {
        // 山登りループの内側にいるためチェック頻度は十分に少なくなる
        if ((loop_cnt & 63) == 0) {
            if (get_time() - start_time > 1.80) break;
        }
        loop_cnt++;

        for(int e = 0; e < all_edges_cnt; ++e) {
            int u = all_edges[e].u, v = all_edges[e].v;
            is_tree_edge[u][v] = is_tree_edge[v][u] = false;
        }

        memset(vis, 0, sizeof(vis));
        int top = 0;
        stack_nodes[top++] = 0;
        vis[0] = true;

        int p_rand_pop = xor_shift() % 30;
        int p_warn = xor_shift() % 100;
        int penalty_399 = ((xor_shift() & 1) == 0) ? 1000000 : 0;

        // --- 1. 初期の木をランダム生成 ---
        while(top > 0) {
            int pop_idx = top - 1;
            if (top > 1 && xor_shift() % 100 < p_rand_pop) pop_idx = xor_shift() % top;
            int u = stack_nodes[pop_idx];

            int nbs[4], nb_cnt = 0;
            for(int e = grid_head[u]; e != -1; e = grid_nxt[e]) if(!vis[grid_to[e]]) nbs[nb_cnt++] = grid_to[e];

            if(nb_cnt > 0) {
                for(int i = 1; i < nb_cnt; ++i) swap(nbs[i], nbs[xor_shift() % (i + 1)]);
                int best_v = nbs[0];
                long long best_score_dfs = -1e18;

                for(int i = 0; i < nb_cnt; ++i) {
                    int v = nbs[i];
                    long long score = xor_shift() % 1000;
                    if (xor_shift() % 100 < p_warn) {
                        int d = 0;
                        for(int e = grid_head[v]; e != -1; e = grid_nxt[e]) if(!vis[grid_to[e]]) d++;
                        score += (10 - d) * 10000LL;
                    }
                    if (v == 399) score -= penalty_399;
                    if (score > best_score_dfs) { best_score_dfs = score; best_v = v; }
                }

                vis[best_v] = true;
                is_tree_edge[u][best_v] = is_tree_edge[best_v][u] = true;
                stack_nodes[top++] = best_v;
            } else {
                stack_nodes[pop_idx] = stack_nodes[--top];
            }
        }

        build_tree_bfs();
        long long cur_W = evaluate_tree_dp(true);

        // --- 2. 木の辺スワップによる山登り (Hill Climbing) ---
        for(int hc = 0; hc < 100; ++hc) {
            int u = -1, v = -1;
            int tries = 0;
            while(tries < 10) {
                int idx = xor_shift() % all_edges_cnt;
                u = all_edges[idx].u; v = all_edges[idx].v;
                if (!is_tree_edge[u][v]) break; // 非木辺を引くまで
                tries++;
            }
            if (is_tree_edge[u][v]) continue;

            // 非木辺(u, v)を足してできる閉路上の辺を探す
            int curr_u = u, curr_v = v;
            int path_u[400], path_v[400];
            int pu_cnt = 0, pv_cnt = 0;
            while (depth[curr_u] > depth[curr_v]) { path_u[pu_cnt++] = curr_u; curr_u = parent_tree[curr_u]; }
            while (depth[curr_v] > depth[curr_u]) { path_v[pv_cnt++] = curr_v; curr_v = parent_tree[curr_v]; }
            while (curr_u != curr_v) {
                path_u[pu_cnt++] = curr_u; curr_u = parent_tree[curr_u];
                path_v[pv_cnt++] = curr_v; curr_v = parent_tree[curr_v];
            }

            int total_edges = pu_cnt + pv_cnt;
            if (total_edges == 0) continue;
            int pick = xor_shift() % total_edges;
            int x, y;
            if (pick < pu_cnt) { x = path_u[pick]; y = parent_tree[x]; }
            else { x = path_v[pick - pu_cnt]; y = parent_tree[x]; }

            // 辺をスワップして新しい木を作る
            is_tree_edge[x][y] = is_tree_edge[y][x] = false;
            is_tree_edge[u][v] = is_tree_edge[v][u] = true;

            build_tree_bfs();
            long long new_W = evaluate_tree_dp(false);

            // スコアが向上、または同じ（構造変化での多様性維持）なら採用
            if (new_W >= cur_W) {
                cur_W = new_W;
                // まともなConfigが生成できそうなら出力候補に追加
                if (new_W > -1e17) { evaluate_tree_dp(true); }
            } else {
                // 悪化したら元に戻す (Revert)
                is_tree_edge[u][v] = is_tree_edge[v][u] = false;
                is_tree_edge[x][y] = is_tree_edge[y][x] = true;
                build_tree_bfs();
            }
        }
    }

    // --- シミュレーション評価フェーズ ---
    long long best_score = -1; vector<Door> final_doors; vector<Switch> final_switches;
    for (auto& conf : top_configs) {
        if (get_time() - start_time > 1.95) break;

        long long T = calc_T(conf.doors, conf.switches);
        if (T > best_score) {
            best_score = T;
            final_doors = conf.doors;
            final_switches = conf.switches;
        }
    }

    if (best_score == -1) { cout << "0\n0\n"; return 0; }

    cout << final_doors.size() << "\n";
    for (auto d : final_doors) cout << d.d << " " << d.i << " " << d.j << " " << d.g << "\n";
    cout << final_switches.size() << "\n";
    for (auto s : final_switches) cout << s.i << " " << s.j << " " << s.s << "\n";

    return 0;
}
