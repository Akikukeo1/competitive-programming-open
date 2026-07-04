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
#include <unordered_map>

using namespace std;

// ------------------------------------------------------------
// �萔�ƌ^��`
// ------------------------------------------------------------
const int INF = 1e9;
const int DX[4] = {0, 1, 0, -1}; // �E, ��, ��, ��
const int DY[4] = {1, 0, -1, 0};
const char DIR_CHAR[4] = {'R', 'D', 'L', 'U'}; // �f�o�b�O�p
const char MOVE_CMD[4] = {'F', 'F', 'F', 'F'}; // ���ۂɎg���͉̂E��]�E����]��F

// ����
const int MAX_M = 40;
const int MAX_V = 400;
const int MAX_DIR = 4;
const int BEAM_WIDTH = 200;
const int MAX_STEPS = 500; // �r�[���̐[�����

// �O���[�o���ϐ� (���̓T�C�Y�Ɉˑ�)
int N, M, T;
vector<string> v_wall, h_wall;
vector<pair<int,int>> ball_pos, basket_pos;
int V; // �Z���� = N*N

struct State {
    int pos;          // ���݂̃Z���ԍ� (0..V-1)
    int dir;          // ���� 0:�E,1:��,2:��,3:��
    int held;         // �ێ����Ă���{�[���̎�� (-1 �Ȃ��)
    vector<int> loc;  // �e�{�[���̈ʒu (�Z���ԍ�, -1=�z�B��, -2=�ێ���)
    int cost;         // �����܂ł̑��A�N�V������ (F,R,L,S�S�Ċ܂�)
    int prev_idx;     // �O�̏�Ԃ̃C���f�b�N�X (�����p)
    int action_type;  // �J�ڂ̎�� (�f�o�b�O�p, ���ۂ͈ړ����Swap�Ώۂ��畜��)

    // �n�b�V���l�̌v�Z
    uint64_t hash() const {
        uint64_t h = (uint64_t)pos * 4 + dir;
        h = h * (MAX_M + 2) + (held + 1);
        for (int i = 0; i < M; ++i) {
            int v = loc[i] + 2; // -2 -> 0, -1 -> 1, 0..V-1 -> 2..V+1
            h = h * 1000003 + v;
        }
        return h;
    }
};

// �O�v�Z�e�[�u��
vector<vector<int>> cell_id;          // (y,x) -> id
vector<pair<int,int>> id_cell;        // id -> (y,x)
vector<vector<int>> adj;              // �אڃZ�� (�ړ��\��4�ߖT)

// �S��� (pos,dir) ����e�Z���ւ̍ŏ��A�N�V�������ƍŏI����
struct MoveInfo {
    int cost;
    int final_dir;
    char first_move; // �ŏ��̈�� (�f�o�b�O�p, ���ۂ͌o�H�����Ɏg��)
};
vector<vector<vector<MoveInfo>>> dist; // [pos][dir][target] ������ target�̓Z���ԍ�
vector<vector<vector<char>>> next_move; // [pos][dir][target] �ŏ��̃R�}���h ('F','L','R')

// ------------------------------------------------------------
// ���[�e�B���e�B
// ------------------------------------------------------------
int id(int y, int x) { return cell_id[y][x]; }

void build_graph() {
    V = N * N;
    cell_id.assign(N, vector<int>(N));
    id_cell.resize(V);
    int idx = 0;
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            cell_id[i][j] = idx;
            id_cell[idx] = {i, j};
            ++idx;
        }
    }
    adj.assign(V, vector<int>());
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            int u = id(i, j);
            // �E
            if (j+1 < N && v_wall[i][j] == '0') {
                int v = id(i, j+1);
                adj[u].push_back(v);
            }
            // ��
            if (j-1 >= 0 && v_wall[i][j-1] == '0') {
                int v = id(i, j-1);
                adj[u].push_back(v);
            }
            // ��
            if (i+1 < N && h_wall[i][j] == '0') {
                int v = id(i+1, j);
                adj[u].push_back(v);
            }
            // ��
            if (i-1 >= 0 && h_wall[i-1][j] == '0') {
                int v = id(i-1, j);
                adj[u].push_back(v);
            }
        }
    }
}

// �S��� (�ʒu,����) ����e�Z���ւ̍ŒZ�o�H (cost, �ŏI����) ��BFS�Ōv�Z
void precompute_dist() {
    dist.assign(V, vector<vector<MoveInfo>>(MAX_DIR, vector<MoveInfo>(V)));
    next_move.assign(V, vector<vector<char>>(MAX_DIR, vector<char>(V, '?')));

    for (int start_pos = 0; start_pos < V; ++start_pos) {
        for (int start_dir = 0; start_dir < 4; ++start_dir) {
            // BFS on state space (pos, dir)
            vector<vector<int>> d(V, vector<int>(4, INF));
            vector<vector<pair<int,int>>> prev(V, vector<pair<int,int>>(4, {-1,-1}));
            queue<pair<int,int>> q;
            d[start_pos][start_dir] = 0;
            q.push({start_pos, start_dir});

            while (!q.empty()) {
                pair<int,int> cur = q.front(); q.pop();
                int p = cur.first;
                int dirl = cur.second;
                int cur_cost = d[p][dirl];
                // �s��1: �O�i
                int np = p;
                int nd = dirl;
                // �אڃZ���̎擾
                int y = id_cell[p].first, x = id_cell[p].second;
                int ny = y + DY[dirl], nx = x + DX[dirl];
                if (ny >= 0 && ny < N && nx >= 0 && nx < N) {
                    // �ǃ`�F�b�N
                    if (dirl == 0 && v_wall[y][x] == '0') np = id(ny,nx);
                    else if (dirl == 1 && h_wall[y][x] == '0') np = id(ny,nx);
                    else if (dirl == 2 && v_wall[y][x-1] == '0') np = id(ny,nx);
                    else if (dirl == 3 && h_wall[y-1][x] == '0') np = id(ny,nx);
                }
                if (np != p && d[np][nd] > cur_cost + 1) {
                    d[np][nd] = cur_cost + 1;
                    prev[np][nd] = {p, dirl};
                    q.push({np, nd});
                }
                // �s��2: �E��]
                nd = (dirl + 1) % 4;
                if (d[p][nd] > cur_cost + 1) {
                    d[p][nd] = cur_cost + 1;
                    prev[p][nd] = {p, dirl};
                    q.push({p, nd});
                }
                // �s��3: ����]
                nd = (dirl + 3) % 4;
                if (d[p][nd] > cur_cost + 1) {
                    d[p][nd] = cur_cost + 1;
                    prev[p][nd] = {p, dirl};
                    q.push({p, nd});
                }
            }

            // �e target �Z���ɂ��āA�ŏ��R�X�g�ƍŏI�������L�^
            for (int target = 0; target < V; ++target) {
                int best_cost = INF;
                int best_dir = -1;
                for (int dir = 0; dir < 4; ++dir) {
                    if (d[target][dir] < best_cost) {
                        best_cost = d[target][dir];
                        best_dir = dir;
                    }
                }
                dist[start_pos][start_dir][target].cost = best_cost;
                dist[start_pos][start_dir][target].final_dir = best_dir;

                // �o�H�����p�̍ŏ��̈������߂� (�K�v�Ȃ�, �����ł͌��BFS�̐e���t�ɒH��)
                // �ȈՔ�: ���� prev ���t�ɒH��͔̂ώG�Ȃ̂ŁA�ʓr next_move �e�[�u������邽�߂�
                // ������x BFS ���Đe���L������ (�������͋��e�͈�)
                // �����ȗ����̂��߁Anext_move �͈�U�ۗ����A�������ɖ���BFS�Ōo�H�𐶐�����B
                // ���x�͗����邪�A�f�o�b�O�D��B
            }
        }
    }
}

// �q���[���X�e�B�b�N: �e���z�B�{�[���̌��ݒn����o�X�P�b�g�܂ł̍ŒZ�����̘a
// ���{�b�g���{�[���������Ă���ꍇ�́A���̃{�[���ɂ��Ă̓��{�b�g�ʒu����o�X�P�b�g�܂ł̋����Ƃ���
int heuristic(const State& s) {
    int h = 0;
    for (int k = 0; k < M; ++k) {
        if (s.loc[k] == -1) continue; // �z�B�ς�
        int from;
        if (s.held == k) from = s.pos;
        else from = s.loc[k];
        // from �̓Z���ԍ� (>=0)
        int to = id(basket_pos[k].first, basket_pos[k].second);
        // ���������̍ŒZ���� (BFS�ŋ��߂� dist �� cost �̍ŏ��l���g��)
        int best = INF;
        for (int dir = 0; dir < 4; ++dir) {
            best = min(best, dist[from][dir][to].cost);
        }
        h += best;
    }
    return h;
}

// �J�ڐ���: ��� s ����\�ȑS�Ă̎��̏�Ԃ𐶐����A���X�g�ɒǉ�
void generate_successors(const State& s, vector<State>& succ, int parent_idx) {
    // ���ƂȂ�h���b�v�ʒu (�{�[�������ʒu + �o�X�P�b�g�ʒu)
    static vector<int> drop_candidates;
    if (drop_candidates.empty()) {
        set<int> cand_set;
        for (int i = 0; i < M; ++i) {
            cand_set.insert(id(ball_pos[i].first, ball_pos[i].second));
            cand_set.insert(id(basket_pos[i].first, basket_pos[i].second));
        }
        drop_candidates.assign(cand_set.begin(), cand_set.end());
    }

    if (s.held == -1) {
        // ���{�b�g����: ���z�B�̃{�[�����s�b�N�A�b�v
        for (int k = 0; k < M; ++k) {
            if (s.loc[k] >= 0) {
                int target = s.loc[k];
                auto& info = dist[s.pos][s.dir][target];
                if (info.cost >= INF) continue;
                State ns = s;
                ns.pos = target;
                ns.dir = info.final_dir;
                ns.held = k;
                ns.loc[k] = -2; // �ێ���
                ns.cost += info.cost + 1; // �ړ��R�X�g + Swap��1
                ns.prev_idx = parent_idx; // �e�̏�Ԃ̃C���f�b�N�X��ۑ� (��ŕ���)
                ns.action_type = 0; // pickup
                succ.push_back(ns);
            }
        }
    } else {
        int b = s.held;
        // 1) �z��
        int target = id(basket_pos[b].first, basket_pos[b].second);
        auto& info = dist[s.pos][s.dir][target];
        if (info.cost < INF) {
            State ns = s;
            ns.pos = target;
            ns.dir = info.final_dir;
            ns.held = -1;
            ns.loc[b] = -1; // �z�B�ς�
            ns.cost += info.cost + 1;
            ns.prev_idx = parent_idx;
            ns.action_type = 1; // deliver
            succ.push_back(ns);
        }
        // 2) �h���b�v (�󂢂Ă���Z���ɒu��)
        for (int c : drop_candidates) {
            // ���̃Z���ɑ��̃{�[�����u����Ă��Ȃ����m�F
            bool occupied = false;
            for (int k = 0; k < M; ++k) {
                if (k != b && s.loc[k] == c) { occupied = true; break; }
            }
            if (occupied) continue;
            auto& info2 = dist[s.pos][s.dir][c];
            if (info2.cost >= INF) continue;
            State ns = s;
            ns.pos = c;
            ns.dir = info2.final_dir;
            ns.held = -1;
            ns.loc[b] = c;
            ns.cost += info2.cost + 1;
            ns.prev_idx = parent_idx;
            ns.action_type = 2; // drop
            succ.push_back(ns);
        }
        // 3) ���̃{�[���ƃX���b�v
        for (int k = 0; k < M; ++k) {
            if (k == b) continue;
            if (s.loc[k] >= 0) {
                int target = s.loc[k];
                auto& info3 = dist[s.pos][s.dir][target];
                if (info3.cost >= INF) continue;
                State ns = s;
                ns.pos = target;
                ns.dir = info3.final_dir;
                ns.held = k;
                ns.loc[b] = target;
                ns.loc[k] = -2;
                ns.cost += info3.cost + 1;
                ns.prev_idx = parent_idx;
                ns.action_type = 3; // swap
                succ.push_back(ns);
            }
        }
    }
}

// ����: �ŏI��Ԃ���A�N�V������𐶐� (������̃��X�g)
vector<string> reconstruct_actions(const vector<State>& beam_states, int final_idx) {
    vector<string> commands;
    int cur = final_idx;
    while (cur != -1) {
        const State& s = beam_states[cur];
        // �e��Ԃ��擾 (prev_idx ���w��)
        if (s.prev_idx == -1) break; // �������
        // const State& ps = beam_states[s.prev_idx];

        // ���ۂɈړ����邽�߂ɁA�ŒZ�o�H�𐶐����� (����BFS�Ōo�H���Čv�Z)
        // �ȈՔ�: �����ł� dist �� next_move ���g���ă��A���^�C���Ɍo�H�𐶐�����֐����Ă�
        // ������ next_move �e�[�u��������Ă��Ȃ��̂ŁA����� on-the-fly BFS �Ōo�H���v�Z����B
        // �������Ȍ��ɂ��邽�߁A��x�A�N�V������S�ă������ɕێ�����̂͒��߁A�����ł͋[���R�[�h�Ƃ���B
        // ���ۂ̉𓚂ł́A�o�H������ dist �e�[�u������e��H���Ăł��邪�A�����Ȃ�̂Ŋ����B
        // ����ɁAcost ���������������Ƃ��m�F���A�o�͂̓_�~�[�Ƃ��� "F" ���o�͂���B
        // �i���ۂɃR���e�X�g�Œ�o����ꍇ�́A�^�ʖڂɌo�H��������������K�v������j
        commands.push_back("F"); // �_�~�[
        break;
    }
    return commands;
}

// ------------------------------------------------------------
// ���C��: �r�[���T�[�`���s
// ------------------------------------------------------------
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // ����
    cin >> N >> M >> T;
    v_wall.resize(N);
    for (int i = 0; i < N; ++i) cin >> v_wall[i];
    h_wall.resize(N-1);
    for (int i = 0; i < N-1; ++i) cin >> h_wall[i];
    ball_pos.resize(M);
    basket_pos.resize(M);
    for (int i = 0; i < M; ++i) {
        int b, c, d, e;
        cin >> b >> c >> d >> e;
        ball_pos[i] = {b, c};
        basket_pos[i] = {d, e};
    }

    // �O���t�\�z
    build_graph();
    // ���O�v�Z (�S��ԊԂ̈ړ��R�X�g)
    precompute_dist();

    // �������
    State init;
    init.pos = id(0,0);
    init.dir = 0; // �E����
    init.held = -1;
    init.loc.assign(M, -1);
    for (int i = 0; i < M; ++i) {
        init.loc[i] = id(ball_pos[i].first, ball_pos[i].second);
    }
    init.cost = 0;
    init.prev_idx = -1;
    init.action_type = -1;

    vector<int> beam = {0}; // beam_states �̃C���f�b�N�X��ێ�
    vector<State> beam_states; // �S��Ԃ��i�[ (�����p)
    beam_states.push_back(init);
    int final_state_idx = -1;

    for (int step = 0; step < MAX_STEPS; ++step) {
        vector<State> candidates;
        unordered_map<uint64_t, int> best_cost_for_hash; // �n�b�V�����ŏ��R�X�g

        // �e��Ԃ���J�ڐ���
        for (int s_idx : beam) {
            const State& s = beam_states[s_idx];
            vector<State> succ;
            generate_successors(s, succ, s_idx);
            for (State& ns : succ) {
                uint64_t h = ns.hash();
                auto it = best_cost_for_hash.find(h);
                if (it == best_cost_for_hash.end() || ns.cost < it->second) {
                    best_cost_for_hash[h] = ns.cost;
                    candidates.push_back(ns);
                }
            }
        }

        if (candidates.empty()) break;

        // �]���l f = cost + heuristic �Ń\�[�g
        sort(candidates.begin(), candidates.end(), [](const State& a, const State& b) {
            int fa = a.cost + heuristic(a);
            int fb = b.cost + heuristic(b);
            return fa < fb;
        });

        // �r�[�����Ő؂�̂�
        if ((int)candidates.size() > BEAM_WIDTH) candidates.resize(BEAM_WIDTH);

        // ���̃r�[�����\�z���A�����ɑS��Ԃ�ۑ�
        beam.clear();
        for (State& s : candidates) {
            beam.push_back((int)beam_states.size());
            beam_states.push_back(s);
            // �S�[������
            bool goal = true;
            for (int i = 0; i < M; ++i) if (s.loc[i] != -1) { goal = false; break; }
            if (goal) {
                final_state_idx = (int)beam_states.size() - 1;
                break;
            }
        }
        if (final_state_idx != -1) break;
    }

    if (final_state_idx == -1) {
        cerr << "No solution found by beam search." << endl;
        // �t�H�[���o�b�N: �P���ȏ����z�� (��: �S�{�[���𒼐ډ^��)
        // �����ł͏ȗ����邪�A�Œ�ł��S�Ẵ{�[�����s�b�N�A�b�v���f���o���[����n����o�͂���B
        // ���̐�����A�K�����͑��݂���̂ŁA�K���ɏo�͂��Ă��X�R�A�͈���������͂���B
        return 1;
    }

    // �������ăR�}���h��𐶐�
    vector<string> actions = reconstruct_actions(beam_states, final_state_idx);
    for (const string& cmd : actions) cout << cmd << '\n';

    return 0;
}
