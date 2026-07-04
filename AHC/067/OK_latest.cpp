#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <chrono>
#include <algorithm>
#include <iomanip>
#include <set>
#include <tuple>

using namespace std;

#pragma region Template
template <class T>
using vc = vector<T>;
template <class T>
using vvc = vector<vector<T>>;
template<class T>
bool chmin(T& a, const T& b){
    if(a > b){
        a = b;
        return true;
    }
    return false;
}
template<class T>
bool chmax(T& a, const T& b){
    if(a < b){
        a = b;
        return true;
    }
    return false;
}

struct Xoshiro256PP {
    uint64_t s[4];

    static uint64_t splitmix64(uint64_t& x) {
        uint64_t z = (x += 0x9e3779b97f4a7c15ULL);
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        return z ^ (z >> 31);
    }

    static uint64_t rotl(const uint64_t x, int k) {
        return (x << k) | (x >> (64 - k));
    }

    Xoshiro256PP() {
        uint64_t seed =
            chrono::steady_clock::now()
            .time_since_epoch()
            .count();

        for (int i = 0; i < 4; i++) {
            s[i] = splitmix64(seed);
        }
    }

    uint64_t operator()() {
        const uint64_t result =
            rotl(s[0] + s[3], 23) + s[0];

        const uint64_t t = s[1] << 17;

        s[2] ^= s[0];
        s[3] ^= s[1];
        s[1] ^= s[2];
        s[0] ^= s[3];

        s[2] ^= t;
        s[3] = rotl(s[3], 45);

        return result;
    }
};
Xoshiro256PP rng;

inline int randint(int l, int r) {
    return l + (int)(rng() % (uint64_t)(r - l + 1));
}

inline double rand01() {
    return (rng() >> 11) * (1.0 / 9007199254740992.0);
}

struct FastIO {
    FastIO() {
        cin.tie(nullptr);
        ios_base::sync_with_stdio(false);
        cout << fixed << setprecision(15);
    }
} fast_io;
#pragma endregion

#pragma region Aliases
using ll = long long;
using pii = pair<int, int>;
using ull = unsigned long long;

constexpr int INF = 1'000'000'001;
constexpr ll LINF = 4'000'000'000'000'000'000LL;

#define OVERLOAD_REP(_1, _2, _3, name, ...) name
#define REP1(i, n) for (auto i = std::decay_t<decltype(n)>{}; (i) != (n); ++(i))
#define REP2(i, l, r) for (auto i = (l); (i) != (r); ++(i))
#define rep(...) OVERLOAD_REP(__VA_ARGS__, REP2, REP1)(__VA_ARGS__)
#define all(...) std::begin(__VA_ARGS__), std::end(__VA_ARGS__)
#define rall(...) std::rbegin(__VA_ARGS__), std::rend(__VA_ARGS__)
#define sz(x) (int)(x).size()
#pragma endregion

// BFSで用いる状態構造体
struct State {
    int mask, i, j;
};

// 扉が開いているか判定
inline bool is_open(int g, int mask) {
    if (g == -1) return true;
    return ((mask >> (g / 2)) & 1) == (g & 1);
}

// 1次元配列で3次元的な距離テーブルを表現して高速化 (1 << K) * N * N
// グローバルまたは動的に確保し、高速化のために 1D vector でフラットに持つ
int calc_T(int N, int K, const vc<string>& c, const vvc<int>& door_h, const vvc<int>& door_v, const vvc<int>& switch_grid) {
    int mask_size = 1 << K;
    int n2 = N * N;
    // -1 で初期化
    vc<int> dist(mask_size * n2, -1);

    dist[0] = 0; // mask=0, i=0, j=0 -> index = 0 * n2 + 0 * N + 0
    queue<State> que;
    que.push({0, 0, 0});

    int di[] = {-1, 1, 0, 0};
    int dj[] = {0, 0, -1, 1};

    while (!que.empty()) {
        State cur = que.front();
        que.pop();

        int idx = cur.mask * n2 + cur.i * N + cur.j;
        int d = dist[idx];

        if (cur.i == N - 1 && cur.j == N - 1) {
            return d;
        }

        // 移動
        rep(k, 4) {
            int ni = cur.i + di[k];
            int nj = cur.j + dj[k];

            if (!(0 <= ni && ni < N && 0 <= nj && nj < N) || c[ni][nj] == '#') {
                continue;
            }

            int g = -1;
            if (di[k] == 1)       g = door_h[cur.i][cur.j];
            else if (di[k] == -1) g = door_h[ni][nj];
            else if (dj[k] == 1)  g = door_v[cur.i][cur.j];
            else                  g = door_v[ni][nj];

            if (!is_open(g, cur.mask)) continue;

            int nidx = cur.mask * n2 + ni * N + nj;
            if (dist[nidx] == -1) {
                dist[nidx] = d + 1;
                que.push({cur.mask, ni, nj});
            }
        }

        // スイッチの操作
        int s = switch_grid[cur.i][cur.j];
        if (s != -1) {
            int nmask = cur.mask ^ (1 << s);
            int nidx = nmask * n2 + cur.i * N + cur.j;
            if (dist[nidx] == -1) {
                dist[nidx] = d + 1;
                que.push({nmask, cur.i, cur.j});
            }
        }
    }
    return 0;
}

void solve() {
    auto start_time = chrono::steady_clock::now();
    double LIMIT = 1.99;

    int N, M, K;
    if (!(cin >> N >> M >> K)) return;

    vc<string> c(N);
    rep(i, N) cin >> c[i];

    vc<pii> empty_cells;
    rep(i, N) {
        rep(j, N) {
            if (c[i][j] == '.') {
                empty_cells.push_back({i, j});
            }
        }
    }

    vvc<int> door_h(N, vc<int>(N, -1));
    vvc<int> door_v(N, vc<int>(N, -1));
    vvc<int> switch_grid(N, vc<int>(N, -1));

    set<pii> fixed_switches;
    set<pii> fixed_doors_h;
    set<pii> fixed_doors_v;
    int door_count = 0;

    // 各マスの次数を計算
    vc<pair<pii, int>> cell_degrees;
    for (auto& cell : empty_cells) {
        int i = cell.first, j = cell.second;
        int deg = 0;
        int di[] = {-1, 1, 0, 0};
        int dj[] = {0, 0, -1, 1};
        rep(k, 4) {
            int ni = i + di[k], nj = j + dj[k];
            if (0 <= ni && ni < N && 0 <= nj && nj < N && c[ni][nj] == '.') {
                deg++;
            }
        }
        cell_degrees.push_back({cell, deg});
    }

    auto place_chain = [&]() {
        if (K == 0) return;

        // 1. ゴールの直前を最後のドアで塞ぐ
        bool goal_door_placed = false;
        if (N >= 2) {
            if (c[N - 2][N - 1] == '.') {
                door_h[N - 2][N - 1] = 2 * (K - 1) + 1;
                fixed_doors_h.insert({N - 2, N - 1});
                door_count++;
                goal_door_placed = true;
            } else if (c[N - 1][N - 2] == '.' && !goal_door_placed) {
                door_v[N - 1][N - 2] = 2 * (K - 1) + 1;
                fixed_doors_v.insert({N - 1, N - 2});
                door_count++;
                goal_door_placed = true;
            }
        }

        // 2. 行き止まりマスを「右上」と「左下」に分離
        vc<pair<pii, int>> tr_candidates;
        vc<pair<pii, int>> bl_candidates;

        for (auto& item : cell_degrees) {
            pii pos = item.first;
            int deg = item.second;
            if (pos == make_pair(0, 0) || pos == make_pair(N - 1, N - 1)) {
                continue;
            }

            if (pos.first + pos.second < N) {
                bl_candidates.push_back(item);
            } else {
                tr_candidates.push_back(item);
            }
        }

        // degの小ささで昇順ソート
        auto cmp = [](const pair<pii, int>& a, const pair<pii, int>& b) {
            return a.second < b.second;
        };
        sort(all(tr_candidates), cmp);
        sort(all(bl_candidates), cmp);

        // 3. 交互に配置
        for (int step = K - 1; step >= 0; step--) {
            vc<pair<pii, int>>* pool = (step % 2 == 1) ? &tr_candidates : &bl_candidates;

            if (pool->empty()) {
                pool = (step % 2 == 1) ? &bl_candidates : &tr_candidates;
            }
            if (pool->empty()) {
                break;
            }

            auto target = pool->front();
            pool->erase(pool->begin());

            int si = target.first.first;
            int sj = target.first.second;
            switch_grid[si][sj] = step;
            fixed_switches.insert({si, sj});

            if (step > 0) {
                int door_val = 2 * (step - 1) + 1;
                int di[] = {-1, 1, 0, 0};
                int dj[] = {0, 0, -1, 1};
                rep(k, 4) {
                    int ni = si + di[k], nj = sj + dj[k];
                    if (0 <= ni && ni < N && 0 <= nj && nj < N && c[ni][nj] == '.') {
                        if (di[k] == 1 && !fixed_doors_h.count({si, sj})) {
                            door_h[si][sj] = door_val;
                            fixed_doors_h.insert({si, sj});
                            door_count++;
                        } else if (di[k] == -1 && !fixed_doors_h.count({ni, nj})) {
                            door_h[ni][nj] = door_val;
                            fixed_doors_h.insert({ni, nj});
                            door_count++;
                        } else if (dj[k] == 1 && !fixed_doors_v.count({si, sj})) {
                            door_v[si][sj] = door_val;
                            fixed_doors_v.insert({si, sj});
                            door_count++;
                        } else if (dj[k] == -1 && !fixed_doors_v.count({ni, nj})) {
                            door_v[ni][nj] = door_val;
                            fixed_doors_v.insert({ni, nj});
                            door_count++;
                        }
                    }
                }
            }
        }
    };

    place_chain();

    int best_T = calc_T(N, K, c, door_h, door_v, switch_grid);

    // 山登りループ
    while (true) {
        auto current_time = chrono::steady_clock::now();
        double elapsed = chrono::duration<double>(current_time - start_time).count();
        if (elapsed >= LIMIT) break;

        int mode = randint(0, 1);

        if (mode == 0) {
            // ドアの追加・削除・変更
            int d_type = randint(0, 1);
            int i = randint(0, N - 1);
            int j = randint(0, N - 1);
            if (d_type == 0 && i == N - 1) continue;
            if (d_type == 1 && j == N - 1) continue;

            if (d_type == 0 && fixed_doors_h.count({i, j})) continue;
            if (d_type == 1 && fixed_doors_v.count({i, j})) continue;

            int old_g = (d_type == 0) ? door_h[i][j] : door_v[i][j];
            int new_g = -1;

            if (old_g != -1 && rand01() < 0.4) {
                new_g = -1;
            } else {
                if (K == 0) continue;
                if (old_g == -1 && door_count >= M) continue;
                // 2*k + 1 (0 <= k < K)
                new_g = 2 * randint(0, K - 1) + 1;
            }

            if (d_type == 0) door_h[i][j] = new_g;
            else             door_v[i][j] = new_g;

            int new_T = calc_T(N, K, c, door_h, door_v, switch_grid);
            if (new_T > best_T) {
                best_T = new_T;
                if (old_g == -1 && new_g != -1) door_count++;
                else if (old_g != -1 && new_g == -1) door_count--;
            } else {
                if (d_type == 0) door_h[i][j] = old_g;
                else             door_v[i][j] = old_g;
            }

        } else {
            // スイッチの追加・削除・変更
            if (K == 0) continue;
            int idx = randint(0, sz(empty_cells) - 1);
            int i = empty_cells[idx].first;
            int j = empty_cells[idx].second;

            if (fixed_switches.count({i, j})) continue;

            int old_s = switch_grid[i][j];
            int new_s = -1;

            if (old_s != -1 && rand01() < 0.3) {
                new_s = -1;
            } else {
                new_s = randint(0, K - 1);
            }

            switch_grid[i][j] = new_s;

            int new_T = calc_T(N, K, c, door_h, door_v, switch_grid);
            if (new_T > best_T) {
                best_T = new_T;
            } else {
                switch_grid[i][j] = old_s;
            }
        }
    }

    // 結果の出力
    vc<tuple<int, int, int, int>> out_doors;
    rep(i, N) {
        rep(j, N) {
            if (door_h[i][j] != -1) out_doors.push_back({0, i, j, door_h[i][j]});
            if (door_v[i][j] != -1) out_doors.push_back({1, i, j, door_v[i][j]});
        }
    }

    vc<tuple<int, int, int>> out_switches;
    rep(i, N) {
        rep(j, N) {
            if (switch_grid[i][j] != -1) out_switches.push_back({i, j, switch_grid[i][j]});
        }
    }

    cout << sz(out_doors) << "\n";
    for (auto& [d, i, j, g] : out_doors) {
        cout << d << " " << i << " " << j << " " << g << "\n";
    }
    cout << sz(out_switches) << "\n";
    for (auto& [p, q, s] : out_switches) {
        cout << p << " " << q << " " << s << "\n";
    }
}

int main() {
    solve();
    return 0;
}
