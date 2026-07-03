#include <iostream> // cout, endl, cin
#include <string> // string, to_string, stoi
#include <vector> // vector
#include <algorithm> // min, max, swap, sort, reverse, lower_bound, upper_bound
#include <utility> // pair, make_pair
#include <tuple> // tuple, make_tuple
#include <cstdint> // int64_t, int*_t
#include <cstdio> // printf
#include <map> // map
#include <queue> // queue, priority_queue
#include <set> // set
#include <stack> // stack
#include <deque> // deque
#include <unordered_map> // unordered_map
#include <unordered_set> // unordered_set
#include <bitset> // bitset
#include <cctype> // isupper, islower, isdigit, toupper, tolower

#include <random>
#include <chrono>
#include <climits>
#include <iomanip>
#include <cstdint>
#include <cstring>

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
        // 浮動小数点の出力精度もついでに固定
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
#define rep(...) OVERLOAD_REP(__VA_ARGS__, REP2, REP1)(__VA_ARGS__)  // repを半開区間専用として使用すること
#define all(...) std::begin(__VA_ARGS__), std::end(__VA_ARGS__)
#define rall(...) std::rbegin(__VA_ARGS__), std::rend(__VA_ARGS__)
#define sz(x) (int)(x).size()
#pragma endregion
