#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <deque>
#include <map>
#include <algorithm>
#include <cmath>
#include <random>
#include <chrono>
#include <tuple>
#include <cstdlib>

using namespace std;

#define rep(i, n) for (int i = 0; i < (int)(n); ++i)
#define all(v) v.begin(), v.end()
#define INF 1000000000

const int DR[] = {-1, 0, 1, 0};
const int DC[] = {0, 1, 0, -1};
const char DIR_NAMES[] = {'U', 'R', 'D', 'L'};

struct Timer {
    chrono::high_resolution_clock::time_point start;
    Timer() { start = chrono::high_resolution_clock::now(); }
    double elapsed() {
        auto now = chrono::high_resolution_clock::now();
        return chrono::duration<double>(now - start).count();
    }
};

struct Random {
    mt19937 engine;
    Random(int seed = 42) : engine(seed) {}
    int next_int(int low, int high) {
        return uniform_int_distribution<int>(low, high - 1)(engine);
    }
    double next_double() {
        return uniform_real_distribution<double>(0.0, 1.0)(engine);
    }
};

int N, M, K;
vector<string> v_walls, h_walls;

bool can_move_forward(int r, int c, int d) {
    if (d == 0) return r > 0 && h_walls[r - 1][c] == '0';
    if (d == 1) return c < N - 1 && v_walls[r][c] == '0';
    if (d == 2) return r < N - 1 && h_walls[r][c] == '0';
    if (d == 3) return c > 0 && v_walls[r][c - 1] == '0';
    return false;
}

struct Node {
    int r, c, d;
};

int adj_dist[205][4][205][4];

double get_env_double(const char* key, double default_val) {
    const char* val = getenv(key);
    if (val == nullptr) return default_val;
    return atof(val);
}

int get_env_int(const char* key, int default_val) {
    const char* val = getenv(key);
    if (val == nullptr) return default_val;
    return atoi(val);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    Timer timer;
    Random rnd;

    if (!(cin >> N >> M >> K)) return 0;

    v_walls.resize(N);
    rep(i, N) cin >> v_walls[i];
    h_walls.resize(N - 1);
    rep(i, N - 1) cin >> h_walls[i];

    vector<pair<int, int>> balls(M), baskets(M);
    vector<pair<int, int>> unique_positions;
    unique_positions.push_back({0, 0});
    map<pair<int, int>, int> pos_to_idx;
    pos_to_idx[{0, 0}] = 0;

    auto add_pos = [&](int r, int c) {
        if (pos_to_idx.find({r, c}) == pos_to_idx.end()) {
            pos_to_idx[{r, c}] = unique_positions.size();
            unique_positions.push_back({r, c});
        }
    };

    rep(i, M) {
        cin >> balls[i].first >> balls[i].second >> baskets[i].first >> baskets[i].second;
        add_pos(balls[i].first, balls[i].second);
        add_pos(baskets[i].first, baskets[i].second);
    }

    int num_unique = unique_positions.size();
    vector<int> ball_indices(M), basket_indices(M);
    rep(i, M) {
        ball_indices[i] = pos_to_idx[balls[i]];
        basket_indices[i] = pos_to_idx[baskets[i]];
    }

    rep(i, num_unique) rep(d, 4) rep(j, num_unique) rep(dd, 4) adj_dist[i][d][j][dd] = INF;

    rep(s_idx, num_unique) {
        rep(sd, 4) {
            int sr = unique_positions[s_idx].first;
            int sc = unique_positions[s_idx].second;

            static int dists[25][25][4];
            rep(r, N) rep(c, N) rep(d, 4) dists[r][c][d] = INF;

            deque<Node> q;
            dists[sr][sc][sd] = 0;
            q.push_back({sr, sc, sd});

            while (!q.empty()) {
                Node curr = q.front(); q.pop_front();
                int r = curr.r, c = curr.c, d = curr.d;
                int curr_d = dists[r][c][d];

                if (can_move_forward(r, c, d)) {
                    int nr = r + DR[d], nc = c + DC[d];
                    if (dists[nr][nc][d] > curr_d + 1) {
                        dists[nr][nc][d] = curr_d + 1;
                        q.push_back({nr, nc, d});
                    }
                }

                int nd_r = (d + 1) % 4;
                if (dists[r][c][nd_r] > curr_d + 1) {
                    dists[r][c][nd_r] = curr_d + 1;
                    q.push_back({r, c, nd_r});
                }
                int nd_l = (d + 3) % 4;
                if (dists[r][c][nd_l] > curr_d + 1) {
                    dists[r][c][nd_l] = curr_d + 1;
                    q.push_back({r, c, nd_l});
                }

                if (can_move_forward(r, c, d)) {
                    int r1 = r + DR[d], c1 = c + DC[d];
                    if (can_move_forward(r1, c1, d)) {
                        int r2 = r1 + DR[d], c2 = c1 + DC[d];
                        if (can_move_forward(r2, c2, d)) {
                            int r3 = r2 + DR[d], c3 = c2 + DC[d];
                            if (dists[r3][c3][d] > curr_d + 1) {
                                dists[r3][c3][d] = curr_d + 1;
                                q.push_back({r3, c3, d});
                            }
                        }
                    }
                }
            }

            rep(d_idx, num_unique) {
                int dr = unique_positions[d_idx].first;
                int dc = unique_positions[d_idx].second;
                rep(dd, 4) adj_dist[s_idx][sd][d_idx][dd] = dists[dr][dc][dd];
            }
        }
    }

    vector<int> state(M);
    rep(i, M) state[i] = i;
    shuffle(all(state), rnd.engine);

    auto get_score = [&](const vector<int>& current_state) {
        int dp[4] = {INF, 0, INF, INF};
        int curr_pos_idx = 0;

        for (int idx : current_state) {
            int b_idx = ball_indices[idx];
            int bk_idx = basket_indices[idx];

            int next_dp_b[4] = {INF, INF, INF, INF};
            rep(d_in, 4) {
                if (dp[d_in] >= INF) continue;
                rep(d_out, 4) {
                    int cost = adj_dist[curr_pos_idx][d_in][b_idx][d_out];
                    next_dp_b[d_out] = min(next_dp_b[d_out], dp[d_in] + cost);
                }
            }
            rep(d, 4) dp[d] = next_dp_b[d] + 1;
            curr_pos_idx = b_idx;

            int next_dp_bk[4] = {INF, INF, INF, INF};
            rep(d_in, 4) {
                if (dp[d_in] >= INF) continue;
                rep(d_out, 4) {
                    int cost = adj_dist[curr_pos_idx][d_in][bk_idx][d_out];
                    next_dp_bk[d_out] = min(next_dp_bk[d_out], dp[d_in] + cost);
                }
            }
            rep(d, 4) dp[d] = next_dp_bk[d] + 1;
            curr_pos_idx = bk_idx;
        }

        int res = INF;
        rep(d, 4) res = min(res, dp[d]);
        return res;
    };

    int current_score = get_score(state);
    vector<int> best_state = state;
    int best_score = current_score;

    double time_limit = get_env_double("SA_TIME_LIMIT", 1.95);
    double t_start = get_env_double("SA_T_START", 15.0);
    double t_end = get_env_double("SA_T_END", 0.05);
    int prob_swap = get_env_int("SA_PROB_SWAP", 40);
    int prob_insert = get_env_int("SA_PROB_INSERT", 40);

    int iter_count = 0;

    while (true) {
        double elapsed = timer.elapsed();
        if (elapsed > time_limit) break;
        iter_count++;

        double temp = t_start * pow(t_end / t_start, elapsed / time_limit);

        int mode = rnd.next_int(0, 100);
        vector<int> next_state = state;
        int i, j;
        if (mode < prob_swap) {
            i = rnd.next_int(0, M);
            j = rnd.next_int(0, M);
            swap(next_state[i], next_state[j]);
        } else if (mode < prob_swap + prob_insert) {
            i = rnd.next_int(0, M);
            int val = next_state[i];
            next_state.erase(next_state.begin() + i);
            j = rnd.next_int(0, M);
            next_state.insert(next_state.begin() + j, val);
        } else {
            i = rnd.next_int(0, M);
            j = rnd.next_int(0, M);
            if (i > j) swap(i, j);
            reverse(next_state.begin() + i, next_state.begin() + j + 1);
        }

        int next_score = get_score(next_state);
        double diff = current_score - next_score;
        if (diff >= 0 || rnd.next_double() < exp(diff / temp)) {
            current_score = next_score;
            state = next_state;
            if (current_score < best_score) {
                best_score = current_score;
                best_state = state;
            }
        }
    }

    auto get_path_with_macro = [&](int sr, int sc, int sd, int tr, int tc, int td) {
        static int dists[25][25][4];
        static pair<Node, string> parents[25][25][4];
        rep(r, N) rep(c, N) rep(d, 4) dists[r][c][d] = INF;
        rep(r, N) rep(c, N) rep(d, 4) parents[r][c][d] = {{-1, -1, -1}, ""};

        deque<Node> q;
        dists[sr][sc][sd] = 0;
        q.push_back({sr, sc, sd});

        while (!q.empty()) {
            Node curr = q.front(); q.pop_front();
            int r = curr.r, c = curr.c, d = curr.d;
            if (r == tr && c == tc && d == td) break;
            int curr_d = dists[r][c][d];

            if (can_move_forward(r, c, d)) {
                int r1 = r + DR[d], c1 = c + DC[d];
                if (can_move_forward(r1, c1, d)) {
                    int r2 = r1 + DR[d], c2 = c1 + DC[d];
                    if (can_move_forward(r2, c2, d)) {
                        int r3 = r2 + DR[d], c3 = c2 + DC[d];
                        if (dists[r3][c3][d] > curr_d + 1) {
                            dists[r3][c3][d] = curr_d + 1;
                            parents[r3][c3][d] = {{r, c, d}, "FFF"};
                            q.push_back({r3, c3, d});
                        }
                    }
                }
            }

            if (can_move_forward(r, c, d)) {
                int nr = r + DR[d], nc = c + DC[d];
                if (dists[nr][nc][d] > curr_d + 1) {
                    dists[nr][nc][d] = curr_d + 1;
                    parents[nr][nc][d] = {{r, c, d}, "F"};
                    q.push_back({nr, nc, d});
                }
            }

            int nd_r = (d + 1) % 4;
            if (dists[r][c][nd_r] > curr_d + 1) {
                dists[r][c][nd_r] = curr_d + 1;
                parents[r][c][nd_r] = {{r, c, d}, "R"};
                q.push_back({r, c, nd_r});
            }
            int nd_l = (d + 3) % 4;
            if (dists[r][c][nd_l] > curr_d + 1) {
                dists[r][c][nd_l] = curr_d + 1;
                parents[r][c][nd_l] = {{r, c, d}, "L"};
                q.push_back({r, c, nd_l});
            }
        }

        vector<string> path;
        int cr = tr, cc = tc, cd = td;
        while (parents[cr][cc][cd].first.r != -1) {
            path.push_back(parents[cr][cc][cd].second);
            Node p = parents[cr][cc][cd].first;
            cr = p.r; cc = p.c; cd = p.d;
        }
        reverse(all(path));
        return path;
    };

    vector<pair<int, vector<int>>> history;
    vector<vector<int>> best_prevs;
    vector<int> dp(4, INF);
    dp[1] = 0;
    history.push_back({0, dp});

    int curr_pos_idx = 0;
    for (int idx : best_state) {
        int target_indices[] = {ball_indices[idx], basket_indices[idx]};
        for (int b_idx : target_indices) {
            vector<int> next_dp(4, INF);
            vector<int> best_prev(4, -1);
            rep(d_in, 4) {
                if (dp[d_in] >= INF) continue;
                rep(d_out, 4) {
                    int cost = adj_dist[curr_pos_idx][d_in][b_idx][d_out];
                    if (dp[d_in] + cost < next_dp[d_out]) {
                        next_dp[d_out] = dp[d_in] + cost;
                        best_prev[d_out] = d_in;
                    }
                }
            }
            history.push_back({b_idx, next_dp});
            best_prevs.push_back(best_prev);
            rep(d, 4) dp[d] = next_dp[d] + 1;
            curr_pos_idx = b_idx;
        }
    }

    int best_last_dir = 0;
    int min_final = INF;
    rep(d, 4) {
        if (history.back().second[d] < min_final) {
            min_final = history.back().second[d];
            best_last_dir = d;
        }
    }

    vector<int> optimal_dirs(history.size());
    int curr_d = best_last_dir;
    for (int i = history.size() - 1; i > 0; --i) {
        optimal_dirs[i] = curr_d;
        curr_d = best_prevs[i - 1][curr_d];
    }
    optimal_dirs[0] = 1;

    vector<string> full_commands;
    for (int i = 1; i < (int)history.size(); ++i) {
        pair<int, int> src = unique_positions[history[i - 1].first];
        pair<int, int> dst = unique_positions[history[i].first];
        vector<string> path = get_path_with_macro(src.first, src.second, optimal_dirs[i - 1], dst.first, dst.second, optimal_dirs[i]);
        for (auto& s : path) {
            if (s == "FFF") full_commands.push_back("FFF_TOKEN");
            else full_commands.push_back(s);
        }
        full_commands.push_back("S");
    }

    int macro_count = 0;
    for (auto& s : full_commands) if (s == "FFF_TOKEN") macro_count++;

    if (macro_count >= 2) {
        bool first = true;
        for (auto& s : full_commands) {
            if (s == "FFF_TOKEN") {
                if (first) {
                    cout << "M\nF\nF\nF\nM\n";
                    first = false;
                } else {
                    cout << "P\n";
                }
            } else {
                cout << s << "\n";
            }
        }
    } else {
        for (auto& s : full_commands) {
            if (s == "FFF_TOKEN") cout << "F\nF\nF\n";
            else cout << s << "\n";
        }
    }

    cerr << "Iterations: " << iter_count << ", Best Score: " << best_score << endl;

    return 0;
}
