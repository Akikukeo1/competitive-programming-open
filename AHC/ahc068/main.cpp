#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>

using namespace std;

// 高速乱数生成器
uint32_t xor_shift() {
    static uint32_t y = 2463534242;
    y ^= (y << 13);
    y ^= (y >> 17);
    return y ^= (y << 5);
}

struct Operation {
    char d;
    int r, c, h, w;
};

// 操作履歴を軽量に保持
struct Trace {
    int parent_idx;
    int op_id;
    int depth;
};

// ビームサーチの各状態（current_pos を保持して O(1) アクセス）
struct State {
    short current_card[400];
    short current_pos[400];
    int score; // 盤面全体のペナルティ (g)
    uint64_t hash_val;
    int trace_idx;
};

// 状態遷移の候補（遅延評価用）
struct Transition {
    int parent_idx;
    int op_id;
    int score; // 次の盤面スコア (g)
    int eval;  // ソート用評価値 (f = g + h + depth)
    short target_pos;
    bool operator<(const Transition& other) const {
        return eval < other.eval;
    }
};

vector<Operation> all_ops;
vector<vector<pair<int, int>>> all_ops_swaps;
vector<pair<int, int>> ops_by_cell[400];
vector<int> adj[400];

int dist_arr[400];
int q_arr[400];
int dist_matrix[400][400];

vector<Trace> trace_log;
uint64_t zobrist[400][400];

// Zobrist Hash の初期化
void init_zobrist() {
    for(int i = 0; i < 400; ++i) {
        for(int j = 0; j < 400; ++j) {
            uint64_t h = xor_shift();
            h = (h << 32) | xor_shift();
            zobrist[i][j] = h;
        }
    }
}

// 全セル間の最短移動距離を事前計算
void precompute_distances(int N) {
    for (int i = 0; i < N * N; ++i) {
        for (int j = 0; j < N * N; ++j) dist_matrix[i][j] = 1e9;
    }
    vector<int> q(N * N);
    for (int start = 0; start < N * N; ++start) {
        int head = 0, tail = 0;
        q[tail++] = start;
        dist_matrix[start][start] = 0;
        while (head < tail) {
            int u = q[head++];
            for (int v : adj[u]) {
                if (dist_matrix[start][v] == 1e9) {
                    dist_matrix[start][v] = dist_matrix[start][u] + 1;
                    q[tail++] = v;
                }
            }
        }
    }
}

// ターゲットセルから逆方向へBFS
void bfs_backward(int target_cell, const vector<uint8_t>& op_active, int N) {
    for(int i = 0; i < N * N; ++i) dist_arr[i] = -1;
    int head = 0, tail = 0;
    q_arr[tail++] = target_cell;
    dist_arr[target_cell] = 0;
    
    while(head < tail) {
        int u = q_arr[head++];
        for(auto& p : ops_by_cell[u]) {
            int op_id = p.first;
            if(op_active[op_id]) {
                int v = p.second;
                if(dist_arr[v] == -1) {
                    dist_arr[v] = dist_arr[u] + 1;
                    q_arr[tail++] = v;
                }
            }
        }
    }
}

int solve_for_root_beam(int root, vector<int>& best_seq_for_root, int limit, const vector<int>& initial_cards, int N, chrono::high_resolution_clock::time_point start_time) {
    vector<int> order;
    vector<bool> vis(N * N, false);
    int head = 0, tail = 0;
    q_arr[tail++] = root;
    vis[root] = true;
    while(head < tail) {
        int u = q_arr[head++];
        order.push_back(u);
        for(int v : adj[u]) {
            if(!vis[v]) {
                vis[v] = true;
                q_arr[tail++] = v;
            }
        }
    }
    reverse(order.begin(), order.end());

    trace_log.clear();
    trace_log.push_back({-1, -1, 0});

    State initial_state;
    initial_state.score = 0;
    initial_state.hash_val = 0;
    initial_state.trace_idx = 0;
    
    for(int i = 0; i < N * N; ++i) {
        initial_state.current_card[i] = initial_cards[i];
        initial_state.current_pos[initial_cards[i]] = i;
        initial_state.score += dist_matrix[i][initial_cards[i]] * 10;
        if(initial_cards[i] == i) initial_state.score -= 15;
        initial_state.hash_val ^= zobrist[i][initial_cards[i]];
    }
    
    vector<State> beam;
    beam.reserve(250);
    beam.push_back(initial_state);
    
    vector<uint8_t> op_active(all_ops.size(), 1);
    
    vector<State> completed;
    vector<Transition> candidates;
    vector<State> next_beam;
    vector<uint64_t> seen_comp;
    vector<uint64_t> seen;
    
    completed.reserve(250);
    candidates.reserve(8000); 
    next_beam.reserve(250);
    seen_comp.reserve(250);
    seen.reserve(250);
    
    for(int step = 0; step < N * N - 1; ++step) {
        double elapsed = chrono::duration<double>(chrono::high_resolution_clock::now() - start_time).count();
        if (step % 5 == 0 && elapsed > 1.95) return 1e9; 
        
        // 安定志向のビーム幅調整
        double remain = 1.95 - elapsed;
        int dynamic_W = 16;
        if (remain > 1.3) dynamic_W = 96;
        else if (remain > 0.8) dynamic_W = 64;
        else if (remain > 0.4) dynamic_W = 48;
        else if (remain > 0.15) dynamic_W = 32;

        int target_cell = order[step];
        int target_card = target_cell;
        
        bfs_backward(target_cell, op_active, N);
        
        while(!beam.empty()) {
            completed.clear();
            candidates.clear();
            
            for(size_t b_idx = 0; b_idx < beam.size(); ++b_idx) {
                const auto& s = beam[b_idx];
                int u = s.current_pos[target_card];
                
                if (u == target_cell) {
                    completed.push_back(s);
                    continue;
                }
                
                int dist_u = dist_arr[u];
                if (dist_u == -1) continue;
                if (trace_log[s.trace_idx].depth >= limit) continue;
                
                for (auto& p : ops_by_cell[u]) {
                    int op_id = p.first;
                    if (!op_active[op_id]) continue;
                    
                    int v = p.second;
                    if (dist_arr[v] == dist_u - 1) {
                        int diff_score = all_ops_swaps[op_id].size(); 
                        short next_target_pos = u;

                        for(auto& swap_pair : all_ops_swaps[op_id]) {
                            int u_s = swap_pair.first;
                            int v_s = swap_pair.second;
                            int c_u = s.current_card[u_s];
                            int c_v = s.current_card[v_s];
                            
                            int d_v_cu = dist_matrix[v_s][c_u];
                            int d_u_cv = dist_matrix[u_s][c_v];
                            int d_u_cu = dist_matrix[u_s][c_u];
                            int d_v_cv = dist_matrix[v_s][c_v];

                            diff_score += (d_v_cu + d_u_cv - d_u_cu - d_v_cv) * 10;
                            diff_score -= ((c_u == v_s) + (c_v == u_s) - (c_u == u_s) - (c_v == v_s)) * 15;
                            
                            if (u_s == u) next_target_pos = v_s;
                            else if (v_s == u) next_target_pos = u_s;
                        }
                        
                        int next_score = s.score + diff_score;
                        int depth = trace_log[s.trace_idx].depth + 1;
                        
                        // 【チューニング】引き込みを 35 にマイルド化、手数を 2 に戻して最適化
                        int eval = next_score + dist_arr[next_target_pos] * 35 + depth * 2;
                        
                        candidates.push_back({(int)b_idx, op_id, next_score, eval, next_target_pos});
                    }
                }
            }
            
            if (!completed.empty()) {
                auto cmp = [](const State& a, const State& b){
                    int depth_a = trace_log[a.trace_idx].depth;
                    int depth_b = trace_log[b.trace_idx].depth;
                    if (depth_a != depth_b) return depth_a < depth_b;
                    return a.score < b.score;
                };
                
                int keep_size = min((int)completed.size(), dynamic_W * 2);
                if ((int)completed.size() > keep_size) {
                    nth_element(completed.begin(), completed.begin() + keep_size, completed.end(), cmp);
                    completed.resize(keep_size);
                }
                sort(completed.begin(), completed.end(), cmp);
                
                seen_comp.clear();
                next_beam.clear();
                for(auto& s : completed) {
                    bool dup = false;
                    for(uint64_t h : seen_comp) if(h == s.hash_val) { dup = true; break; }
                    if(!dup) {
                        seen_comp.push_back(s.hash_val);
                        next_beam.push_back(s);
                        if(next_beam.size() == dynamic_W) break;
                    }
                }
                beam.swap(next_beam);
                break;
            }
            
            if (candidates.empty()) {
                beam.clear();
                break;
            }
            
            int current_W = dynamic_W;
            if (candidates.size() <= 64) {
                current_W = candidates.size(); 
            } else if (candidates.size() > 600) {
                current_W = max(16, dynamic_W * 4 / 5); 
            }
            
            if (candidates.size() <= current_W) {
                sort(candidates.begin(), candidates.end());
            } else {
                int keep_size = min((int)candidates.size(), current_W * 2);
                nth_element(candidates.begin(), candidates.begin() + keep_size, candidates.end());
                candidates.resize(keep_size);
                sort(candidates.begin(), candidates.end());
            }
            
            next_beam.clear();
            seen.clear();
            
            for(auto& cand : candidates) {
                const auto& s = beam[cand.parent_idx];
                
                uint64_t next_hash = s.hash_val;
                for(auto& swap_pair : all_ops_swaps[cand.op_id]) {
                    int u_s = swap_pair.first;
                    int v_s = swap_pair.second;
                    int c_u = s.current_card[u_s];
                    int c_v = s.current_card[v_s];
                    next_hash ^= zobrist[u_s][c_u] ^ zobrist[v_s][c_v] ^ zobrist[u_s][c_v] ^ zobrist[v_s][c_u];
                }
                
                bool dup = false;
                for(uint64_t h : seen) {
                    if(h == next_hash) { dup = true; break; }
                }
                if(dup) continue;
                
                seen.push_back(next_hash);
                
                State next_s = s;
                next_s.score = cand.score;
                next_s.hash_val = next_hash;
                
                trace_log.push_back({s.trace_idx, cand.op_id, trace_log[s.trace_idx].depth + 1});
                next_s.trace_idx = (int)trace_log.size() - 1;
                
                for(auto& swap_pair : all_ops_swaps[cand.op_id]) {
                    int u_s = swap_pair.first;
                    int v_s = swap_pair.second;
                    int c_u = next_s.current_card[u_s];
                    int c_v = next_s.current_card[v_s];
                    
                    next_s.current_card[u_s] = c_v;
                    next_s.current_card[v_s] = c_u;
                    next_s.current_pos[c_u] = v_s;
                    next_s.current_pos[c_v] = u_s;
                }
                
                next_beam.push_back(next_s);
                if(next_beam.size() == current_W) break;
            }
            beam.swap(next_beam);
        }
        
        if (beam.empty()) return 1e9;
        
        for(auto& p : ops_by_cell[target_cell]) op_active[p.first] = 0;
    }
    
    int best_idx = 0;
    for(size_t i = 1; i < beam.size(); ++i) {
        if (trace_log[beam[i].trace_idx].depth < trace_log[beam[best_idx].trace_idx].depth) {
            best_idx = i;
        }
    }
    
    best_seq_for_root.clear();
    int curr = beam[best_idx].trace_idx;
    while(curr != -1) {
        int op = trace_log[curr].op_id;
        if (op != -1) best_seq_for_root.push_back(op);
        curr = trace_log[curr].parent_idx;
    }
    reverse(best_seq_for_root.begin(), best_seq_for_root.end());
    
    return best_seq_for_root.size();
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    auto start_time = chrono::high_resolution_clock::now();

    init_zobrist();
    trace_log.reserve(2500000); 

    int N;
    if (!(cin >> N)) return 0;

    vector<int> initial_cards(N * N);
    for(int i = 0; i < N * N; ++i) cin >> initial_cards[i];

    vector<string> V(N);
    for(int i = 0; i < N; ++i) cin >> V[i];
    vector<string> H(N - 1);
    for(int i = 0; i < N - 1; ++i) cin >> H[i];

    for (char d : {'V', 'H'}) {
        for (int r = 0; r < N; ++r) {
            for (int c = 0; c < N; ++c) {
                for (int h = 1; r + h <= N; ++h) {
                    for (int w = 1; c + w <= N; ++w) {
                        if (d == 'V' && h % 2 != 0) continue;
                        if (d == 'H' && w % 2 != 0) continue;

                        bool valid = true;
                        for(int i = r; i < r + h - 1; ++i)
                            for(int j = c; j < c + w; ++j)
                                if(H[i][j] == '1') valid = false;
                        for(int i = r; i < r + h; ++i)
                            for(int j = c; j < c + w - 1; ++j)
                                if(V[i][j] == '1') valid = false;

                        if(!valid) continue;

                        int op_id = all_ops.size();
                        all_ops.push_back({d, r, c, h, w});
                        vector<pair<int, int>> swaps;

                        if (d == 'V') {
                            for(int x = 0; x < h / 2; ++x) {
                                for(int y = 0; y < w; ++y) {
                                    int u = (r + x) * N + (c + y);
                                    int v = (r + h / 2 + x) * N + (c + y);
                                    swaps.push_back({u, v});
                                }
                            }
                        } else {
                            for(int x = 0; x < h; ++x) {
                                for(int y = 0; y < w / 2; ++y) {
                                    int u = (r + x) * N + (c + y);
                                    int v = (r + x) * N + (c + w / 2 + y);
                                    swaps.push_back({u, v});
                                }
                            }
                        }

                        all_ops_swaps.push_back(swaps);
                        for(auto& p : swaps) {
                            ops_by_cell[p.first].push_back({op_id, p.second});
                            ops_by_cell[p.second].push_back({op_id, p.first});
                            if (h * w == 2) {
                                adj[p.first].push_back(p.second);
                                adj[p.second].push_back(p.first);
                            }
                        }
                    }
                }
            }
        }
    }

    precompute_distances(N);

    int best_total_ops = 1e9;
    vector<int> best_sequence;

    vector<int> roots(N * N);
    for(int i = 0; i < N * N; ++i) roots[i] = i;
    sort(roots.begin(), roots.end(), [N](int a, int b) {
        return abs(a / N - (N/2-1)) + abs(a % N - (N/2-1)) < abs(b / N - (N/2-1)) + abs(b % N - (N/2-1));
    });

    vector<pair<int, int>> root_scores;

    for(int root : roots) {
        vector<int> seq;
        int limit = (best_total_ops == 1e9) ? 1e9 : best_total_ops + 400; 
        int ops = solve_for_root_beam(root, seq, limit, initial_cards, N, start_time);
        
        if(ops < best_total_ops) {
            best_total_ops = ops;
            best_sequence = seq;
        }
        if (ops != 1e9) root_scores.push_back({ops, root});

        auto current_time = chrono::high_resolution_clock::now();
        if(chrono::duration<double>(current_time - start_time).count() > 1.83) break;
    }

    if (!root_scores.empty()) {
        sort(root_scores.begin(), root_scores.end());
        int num_top_roots = min(20, (int)root_scores.size()); 

        while(true) {
            auto current_time = chrono::high_resolution_clock::now();
            if(chrono::duration<double>(current_time - start_time).count() > 1.91) break; 

            int root = root_scores[xor_shift() % num_top_roots].second;

            for(int i = 0; i < N * N; ++i) {
                int sz = ops_by_cell[i].size();
                if(sz > 1) {
                    int shuffle_count = min(sz - 1, 30);
                    for(int k = 0; k < shuffle_count; ++k) {
                        int j = k + xor_shift() % (sz - k);
                        swap(ops_by_cell[i][k], ops_by_cell[i][j]);
                    }
                }
            }

            vector<int> seq;
            int ops = solve_for_root_beam(root, seq, best_total_ops, initial_cards, N, start_time);
            if(ops < best_total_ops) {
                best_total_ops = ops;
                best_sequence = seq;
            }
        }
    }

    if (best_sequence.size() > 100000) best_sequence.resize(100000);

    for (int op_id : best_sequence) {
        Operation& op = all_ops[op_id];
        cout << op.d << " " << op.r << " " << op.c << " " << op.h << " " << op.w << "\n";
    }

    return 0;
}