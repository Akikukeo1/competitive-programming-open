#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <random>
#include <map>
#include <set>

using namespace std;

// 定数
const int DR[] = {-1, 0, 1, 0}; // 上, 右, 下, 左
const int DC[] = {0, 1, 0, -1};
const string DIR_NAMES[] = {"U", "R", "D", "L"};
const int INF = 1e9;

// グローバル変数/キャッシュ
int N, M, T_limit_in;
vector<string> v_walls;
vector<string> h_walls;
struct Pos {
    int r, c;
    bool operator<(const Pos& other) const {
        if (r != other.r) return r < other.r;
        return c < other.c;
    }
    bool operator==(const Pos& other) const {
        return r == other.r && c == other.c;
    }
};

vector<Pos> unique_positions;
map<Pos, int> pos_to_idx;
vector<int> ball_indices;
vector<int> basket_indices;
int adj_dist[205][4][205][4]; // [from_idx][from_dir][to_idx][to_dir]

// 壁判定
bool can_move_forward(int r, int c, int d) {
    if (d == 0) return r > 0 && h_walls[r - 1][c] == '0';
    if (d == 1) return c < N - 1 && v_walls[r][c] == '0';
    if (d == 2) return r < N - 1 && h_walls[r][c] == '0';
    if (d == 3) return c > 0 && v_walls[r][c - 1] == '0';
    return false;
}

// SA 用のスコア計算
int get_score(const vector<int>& state) {
    int dp[4] = {INF, 0, INF, INF};
    int curr_pos_idx = 0;
    for (int idx : state) {
        int b_idx = ball_indices[idx];
        int nxt[4] = {INF, INF, INF, INF};
        for (int d_in = 0; d_in < 4; ++d_in) {
            if (dp[d_in] >= INF) continue;
            for (int d_out = 0; d_out < 4; ++d_out) {
                int cost = adj_dist[curr_pos_idx][d_in][b_idx][d_out];
                if (dp[d_in] + cost < nxt[d_out]) nxt[d_out] = dp[d_in] + cost;
            }
        }
        for (int d = 0; d < 4; ++d) dp[d] = nxt[d] + 1;
        curr_pos_idx = b_idx;

        int bk_idx = basket_indices[idx];
        for (int d = 0; d < 4; ++d) nxt[d] = INF;
        for (int d_in = 0; d_in < 4; ++d_in) {
            if (dp[d_in] >= INF) continue;
            for (int d_out = 0; d_out < 4; ++d_out) {
                int cost = adj_dist[curr_pos_idx][d_in][bk_idx][d_out];
                if (dp[d_in] + cost < nxt[d_out]) nxt[d_out] = dp[d_in] + cost;
            }
        }
        for (int d = 0; d < 4; ++d) dp[d] = nxt[d] + 1;
        curr_pos_idx = bk_idx;
    }
    int res = INF;
    for (int d = 0; d < 4; ++d) if (dp[d] < res) res = dp[d];
    return res;
}

struct Parent {
    int r, c, d;
    string cmd;
};

vector<string> get_path_with_macro(int sr, int sc, int sd, int tr, int tc, int td) {
    int dists[30][30][4];
    Parent parents[30][30][4];
    for(int i=0; i<N; ++i) for(int j=0; j<N; ++j) for(int d=0; d<4; ++d) dists[i][j][d] = INF;

    queue<pair<pair<int, int>, int>> q;
    q.push({{sr, sc}, sd});
    dists[sr][sc][sd] = 0;

    while (!q.empty()) {
        auto curr = q.front(); q.pop();
        int r = curr.first.first, c = curr.first.second, d = curr.second;
        if (r == tr && c == tc && d == td) break;
        int curr_d = dists[r][c][d];

        // FFF
        if (can_move_forward(r, c, d)) {
            int r1 = r + DR[d], c1 = c + DC[d];
            if (can_move_forward(r1, c1, d)) {
                int r2 = r1 + DR[d], c2 = c1 + DC[d];
                if (can_move_forward(r2, c2, d)) {
                    int r3 = r2 + DR[d], c3 = c2 + DC[d];
                    if (dists[r3][c3][d] > curr_d + 1) {
                        dists[r3][c3][d] = curr_d + 1;
                        parents[r3][c3][d] = {r, c, d, "FFF"};
                        q.push({{r3, c3}, d});
                    }
                }
            }
        }

        // F
        if (can_move_forward(r, c, d)) {
            int nr = r + DR[d], nc = c + DC[d];
            if (dists[nr][nc][d] > curr_d + 1) {
                dists[nr][nc][d] = curr_d + 1;
                parents[nr][nc][d] = {r, c, d, "F"};
                q.push({{nr, nc}, d});
            }
        }

        // R, L
        int nd_r = (d + 1) % 4;
        if (dists[r][c][nd_r] > curr_d + 1) {
            dists[r][c][nd_r] = curr_d + 1;
            parents[r][c][nd_r] = {r, c, d, "R"};
            q.push({{r, c}, nd_r});
        }
        int nd_l = (d + 3) % 4;
        if (dists[r][c][nd_l] > curr_d + 1) {
            dists[r][c][nd_l] = curr_d + 1;
            parents[r][c][nd_l] = {r, c, d, "L"};
            q.push({{r, c}, nd_l});
        }
    }

    vector<string> path;
    int cr = tr, cc = tc, cd = td;
    while (!(cr == sr && cc == sc && cd == sd)) {
        Parent p = parents[cr][cc][cd];
        path.push_back(p.cmd);
        cr = p.r; cc = p.c; cd = p.d;
    }
    reverse(path.begin(), path.end());
    return path;
}

int main() {
    auto start_time = chrono::system_clock::now();
    
    if (!(cin >> N >> M >> T_limit_in)) return 0;
    v_walls.resize(N);
    for (int i = 0; i < N; ++i) cin >> v_walls[i];
    h_walls.resize(N - 1);
    for (int i = 0; i < N - 1; ++i) cin >> h_walls[i];

    vector<Pos> balls(M), baskets(M);
    unique_positions.push_back({0, 0});
    pos_to_idx[{0, 0}] = 0;

    for (int i = 0; i < M; ++i) {
        cin >> balls[i].r >> balls[i].c >> baskets[i].r >> baskets[i].c;
        if (pos_to_idx.find(balls[i]) == pos_to_idx.end()) {
            pos_to_idx[balls[i]] = unique_positions.size();
            unique_positions.push_back(balls[i]);
        }
        if (pos_to_idx.find(baskets[i]) == pos_to_idx.end()) {
            pos_to_idx[baskets[i]] = unique_positions.size();
            unique_positions.push_back(baskets[i]);
        }
    }

    int num_unique = unique_positions.size();
    ball_indices.resize(M);
    basket_indices.resize(M);
    for (int i = 0; i < M; ++i) {
        ball_indices[i] = pos_to_idx[balls[i]];
        basket_indices[i] = pos_to_idx[baskets[i]];
    }

    // 1. 全点対最短経路 (拡張BFS)
    for (int s_idx = 0; s_idx < num_unique; ++s_idx) {
        Pos s = unique_positions[s_idx];
        for (int sd = 0; sd < 4; ++sd) {
            int dists[30][30][4];
            for(int i=0; i<N; ++i) for(int j=0; j<N; ++j) for(int d=0; d<4; ++d) dists[i][j][d] = INF;
            
            queue<pair<pair<int, int>, int>> q;
            q.push({{s.r, s.c}, sd});
            dists[s.r][s.c][sd] = 0;

            while (!q.empty()) {
                auto curr = q.front(); q.pop();
                int r = curr.first.first, c = curr.first.second, d = curr.second;
                int curr_d = dists[r][c][d];

                // FFF
                if (can_move_forward(r, c, d)) {
                    int r1 = r + DR[d], c1 = c + DC[d];
                    if (can_move_forward(r1, c1, d)) {
                        int r2 = r1 + DR[d], c2 = c1 + DC[d];
                        if (can_move_forward(r2, c2, d)) {
                            int r3 = r2 + DR[d], c3 = c2 + DC[d];
                            if (dists[r3][c3][d] > curr_d + 1) {
                                dists[r3][c3][d] = curr_d + 1;
                                q.push({{r3, c3}, d});
                            }
                        }
                    }
                }
                // F
                if (can_move_forward(r, c, d)) {
                    int nr = r + DR[d], nc = c + DC[d];
                    if (dists[nr][nc][d] > curr_d + 1) {
                        dists[nr][nc][d] = curr_d + 1;
                        q.push({{nr, nc}, d});
                    }
                }
                // R, L
                int nd_r = (d + 1) % 4;
                if (dists[r][c][nd_r] > curr_d + 1) {
                    dists[r][c][nd_r] = curr_d + 1;
                    q.push({{r, c}, nd_r});
                }
                int nd_l = (d + 3) % 4;
                if (dists[r][c][nd_l] > curr_d + 1) {
                    dists[r][c][nd_l] = curr_d + 1;
                    q.push({{r, c}, nd_l});
                }
            }
            for (int d_idx = 0; d_idx < num_unique; ++d_idx) {
                Pos target = unique_positions[d_idx];
                for (int dd = 0; dd < 4; ++dd) {
                    adj_dist[s_idx][sd][d_idx][dd] = dists[target.r][target.c][dd];
                }
            }
        }
    }

    // 2. 焼きなまし法 (SA)
    mt19937 engine(42);
    vector<int> state(M);
    for (int i = 0; i < M; ++i) state[i] = i;
    shuffle(state.begin(), state.end(), engine);

    int current_score = get_score(state);
    vector<int> best_state = state;
    int best_score = current_score;

    double t_start = 15.0, t_end = 0.05;
    double time_limit = 1.9; // ユーザー指定の 1.9s
    int iter_count = 0;

    uniform_real_distribution<double> dist_u(0.0, 1.0);

    while (true) {
        auto now = chrono::system_clock::now();
        double elapsed = chrono::duration_cast<chrono::milliseconds>(now - start_time).count() / 1000.0;
        if (elapsed > time_limit) break;
        iter_count++;

        double t = t_start * pow(t_end / t_start, elapsed / time_limit);
        double mode = dist_u(engine);

        if (mode < 0.4) {
            int i = uniform_int_distribution<int>(0, M - 1)(engine);
            int j = uniform_int_distribution<int>(0, M - 1)(engine);
            if (i == j) continue;
            swap(state[i], state[j]);
            int n_score = get_score(state);
            if (n_score < current_score || dist_u(engine) < exp((current_score - n_score) / t)) {
                current_score = n_score;
                if (current_score < best_score) { best_score = current_score; best_state = state; }
            } else {
                swap(state[i], state[j]);
            }
        } else if (mode < 0.8) {
            int i = uniform_int_distribution<int>(0, M - 1)(engine);
            int val = state[i];
            state.erase(state.begin() + i);
            int j = uniform_int_distribution<int>(0, M - 1)(engine);
            state.insert(state.begin() + j, val);
            int n_score = get_score(state);
            if (n_score < current_score || dist_u(engine) < exp((current_score - n_score) / t)) {
                current_score = n_score;
                if (current_score < best_score) { best_score = current_score; best_state = state; }
            } else {
                state.erase(state.begin() + j);
                state.insert(state.begin() + i, val);
            }
        } else {
            int i = uniform_int_distribution<int>(0, M - 1)(engine);
            int j = uniform_int_distribution<int>(0, M - 1)(engine);
            if (i > j) swap(i, j);
            reverse(state.begin() + i, state.begin() + j + 1);
            int n_score = get_score(state);
            if (n_score < current_score || dist_u(engine) < exp((current_score - n_score) / t)) {
                current_score = n_score;
                if (current_score < best_score) { best_score = current_score; best_state = state; }
            } else {
                reverse(state.begin() + i, state.begin() + j + 1);
            }
        }
    }

    // 3. リロケーション
    vector<vector<int>> min_dist_table(num_unique, vector<int>(num_unique, INF));
    for (int u = 0; u < num_unique; ++u) {
        for (int v = 0; v < num_unique; ++v) {
            for (int d1 = 0; d1 < 4; ++d1) {
                for (int d2 = 0; d2 < 4; ++d2) {
                    min_dist_table[u][v] = min(min_dist_table[u][v], adj_dist[u][d1][v][d2]);
                }
            }
        }
    }

    vector<pair<double, int>> centrality;
    for (int u = 0; u < num_unique; ++u) {
        double sum_d = 0;
        for (int k = 0; k < M; ++k) sum_d += min_dist_table[u][basket_indices[k]];
        centrality.push_back({sum_d / M, u});
    }
    sort(centrality.begin(), centrality.end());
    vector<int> top_hubs;
    for (int i = 0; i < min(10, (int)centrality.size()); ++i) top_hubs.push_back(centrality[i].second);

    struct Reloc { int j_id, old_p, new_v; };
    map<int, Reloc> relocations;
    vector<int> curr_ball_indices = ball_indices;
    int curr_pos_idx = 0;
    for (int i = 0; i < M; ++i) {
        int best_j = -1, best_v = -1;
        double max_gain = -1;
        for (int k = 1; k <= 3; ++k) {
            if (i + k >= M) break;
            int j_id = best_state[i + k];
            int pos_j_idx = curr_ball_indices[j_id];
            int target_j_idx = basket_indices[j_id];
            int prev_j_bk_idx = basket_indices[best_state[i + k - 1]];

            vector<int> candidates_v = {curr_ball_indices[best_state[i]], basket_indices[best_state[i]]};
            if (i + 1 < M) candidates_v.push_back(basket_indices[best_state[i + 1]]);
            for (int h : top_hubs) candidates_v.push_back(h);

            set<int> seen_v;
            for (int v_idx : candidates_v) {
                if (v_idx == pos_j_idx || seen_v.count(v_idx)) continue;
                seen_v.insert(v_idx);
                double inc = min_dist_table[curr_pos_idx][pos_j_idx] + min_dist_table[pos_j_idx][v_idx] + 2 - min_dist_table[curr_pos_idx][v_idx];
                double old_c = min_dist_table[prev_j_bk_idx][pos_j_idx] + min_dist_table[pos_j_idx][target_j_idx];
                double new_c = min_dist_table[prev_j_bk_idx][v_idx] + min_dist_table[v_idx][target_j_idx];
                double gain = old_c - new_c - inc;
                if (gain > max_gain) { max_gain = gain; best_j = j_id; best_v = v_idx; }
            }
        }
        if (best_j != -1 && max_gain > 5) {
            relocations[i] = {best_j, curr_ball_indices[best_j], best_v};
            curr_ball_indices[best_j] = best_v;
        }
        curr_pos_idx = basket_indices[best_state[i]];
    }
    vector<int> final_ball_indices = curr_ball_indices;

    // 4. 最終経路計算 (DPによる向き最適化)
    vector<int> dp(4, INF); dp[1] = 0;
    struct Hist { int pos_idx; vector<int> dps; vector<int> prev_d; };
    vector<Hist> history;
    history.push_back({0, {INF, 0, INF, INF}, {-1, -1, -1, -1}});

    curr_pos_idx = 0;
    for (int idx : best_state) {
        // to Ball
        int b_idx = final_ball_indices[idx];
        vector<int> nxt(4, INF), best_p(4, -1);
        for(int d_in=0; d_in<4; ++d_in) {
            if (dp[d_in] >= INF) continue;
            for(int d_out=0; d_out<4; ++d_out) {
                int cost = adj_dist[curr_pos_idx][d_in][b_idx][d_out];
                if (dp[d_in] + cost < nxt[d_out]) { nxt[d_out] = dp[d_in] + cost; best_p[d_out] = d_in; }
            }
        }
        for(int d=0; d<4; ++d) nxt[d]++;
        history.push_back({b_idx, nxt, best_p});
        dp = nxt; curr_pos_idx = b_idx;

        // to Basket
        int bk_idx = basket_indices[idx];
        nxt.assign(4, INF); best_p.assign(4, -1);
        for(int d_in=0; d_in<4; ++d_in) {
            if (dp[d_in] >= INF) continue;
            for(int d_out=0; d_out<4; ++d_out) {
                int cost = adj_dist[curr_pos_idx][d_in][bk_idx][d_out];
                if (dp[d_in] + cost < nxt[d_out]) { nxt[d_out] = dp[d_in] + cost; best_p[d_out] = d_in; }
            }
        }
        for(int d=0; d<4; ++d) nxt[d]++;
        history.push_back({bk_idx, nxt, best_p});
        dp = nxt; curr_pos_idx = bk_idx;
    }

    int best_last_dir = 0, min_f = INF;
    for(int d=0; d<4; ++d) if (history.back().dps[d] < min_f) { min_f = history.back().dps[d]; best_last_dir = d; }
    vector<int> optimal_dirs(history.size());
    int cd = best_last_dir;
    for(int i=history.size()-1; i>=0; --i) {
        optimal_dirs[i] = cd;
        cd = history[i].prev_d[cd];
    }
    optimal_dirs[0] = 1;

    vector<string> full_commands;
    for (int i = 1; i < (int)history.size(); ++i) {
        Pos src = unique_positions[history[i-1].pos_idx];
        Pos dst = unique_positions[history[i].pos_idx];
        int step_idx = (i - 1) / 2;
        if (i % 2 == 1 && relocations.count(step_idx)) {
            Reloc r = relocations[step_idx];
            Pos p_j = unique_positions[r.old_p];
            Pos n_v = unique_positions[r.new_v];
            auto p1 = get_path_with_macro(src.r, src.c, optimal_dirs[i-1], p_j.r, p_j.c, 0);
            for(auto& c : p1) full_commands.push_back(c);
            full_commands.push_back("S");
            auto p2 = get_path_with_macro(p_j.r, p_j.c, 0, n_v.r, n_v.c, 0);
            for(auto& c : p2) full_commands.push_back(c);
            full_commands.push_back("S");
            auto p3 = get_path_with_macro(n_v.r, n_v.c, 0, dst.r, dst.c, optimal_dirs[i]);
            for(auto& c : p3) full_commands.push_back(c);
        } else {
            auto path = get_path_with_macro(src.r, src.c, optimal_dirs[i-1], dst.r, dst.c, optimal_dirs[i]);
            for(auto& c : path) full_commands.push_back(c);
        }
        full_commands.push_back("S");
    }

    int macro_count = 0;
    for(auto& c : full_commands) if(c == "FFF") macro_count++;

    if (macro_count >= 2) {
        bool first = true;
        for (auto& c : full_commands) {
            if (c == "FFF") {
                if (first) { cout << "M\nF\nF\nF\nM\n"; first = false; }
                else cout << "P\n";
            } else cout << c << "\n";
        }
    } else {
        for (auto& c : full_commands) {
            if (c == "FFF") cout << "F\nF\nF\n";
            else cout << c << "\n";
        }
    }

    cerr << "Iterations: " << iter_count << ", Best Score: " << best_score << endl;
    return 0;
}
