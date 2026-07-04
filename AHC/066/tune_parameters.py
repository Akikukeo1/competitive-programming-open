import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
import optuna


@dataclass(frozen=True)
class SolverParams:
    sa_time_limit: float = 1.95
    sa_t_start: float = 15.0
    sa_t_end: float = 0.05
    sa_prob_swap: int = 40
    sa_prob_insert: int = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="main_optuna.cpp のパラメータを Optuna で探索する")
    parser.add_argument(
        "inputs",
        nargs="*",
        default=[f"in/{i:04d}.txt" for i in range(10)],
        help="評価に使う入力ファイル（in/0000.txt など）",
    )
    parser.add_argument("--trials", type=int, default=50, help="Optuna の試行回数")
    parser.add_argument("--timeout", type=float, default=None, help="Optuna 全体の制限時間（秒）")
    parser.add_argument("--seed", type=int, default=42, help="Optuna の乱数シード")
    return parser.parse_args()


def read_input_text(input_path: Path) -> str:
    return input_path.read_text(encoding="utf-8")


def parse_input(input_text: str):
    tokens = input_text.split()
    if not tokens:
        raise ValueError("入力が空です")

    iterator = iter(tokens)
    n = int(next(iterator))
    m = int(next(iterator))
    t_limit = int(next(iterator))
    v_walls = [next(iterator) for _ in range(n)]
    h_walls = [next(iterator) for _ in range(n - 1)]

    balls = []
    baskets = []
    for _ in range(m):
        r1, c1, r2, c2 = (int(next(iterator)) for _ in range(4))
        balls.append((r1, c1))
        baskets.append((r2, c2))

    return n, m, t_limit, v_walls, h_walls, balls, baskets


def simulate_score(input_text: str, commands: list[str]) -> tuple[int, int, int]:
    n, m, t_limit, v_walls, h_walls, balls, baskets = parse_input(input_text)

    def can_move(r: int, c: int, direction: int) -> bool:
        if direction == 0:
            return r > 0 and h_walls[r - 1][c] == "0"
        if direction == 1:
            return c < n - 1 and v_walls[r][c] == "0"
        if direction == 2:
            return r < n - 1 and h_walls[r][c] == "0"
        if direction == 3:
            return c > 0 and v_walls[r][c - 1] == "0"
        return False

    robot_r, robot_c, robot_dir = 0, 0, 1
    holding_ball = None
    ball_at = {pos: idx for idx, pos in enumerate(balls)}
    registered_macro = []
    recording = False
    recording_buffer = []
    executed_base_steps = 0

    def execute_command(command: str):
        nonlocal robot_r, robot_c, robot_dir, holding_ball
        nonlocal recording, registered_macro, recording_buffer, executed_base_steps

        if executed_base_steps >= t_limit:
            return
        if command == "M":
            if recording:
                registered_macro = recording_buffer[:]
                recording = False
            else:
                recording = True
                recording_buffer = []
            return
        if command == "P":
            if registered_macro:
                for nested_command in registered_macro:
                    if executed_base_steps >= t_limit:
                        break
                    execute_command(nested_command)
            return
        if recording:
            recording_buffer.append(command)
        executed_base_steps += 1
        if command == "F":
            if can_move(robot_r, robot_c, robot_dir):
                robot_r += (-1, 0, 1, 0)[robot_dir]
                robot_c += (0, 1, 0, -1)[robot_dir]
        elif command == "R":
            robot_dir = (robot_dir + 1) % 4
        elif command == "L":
            robot_dir = (robot_dir - 1) % 4
        elif command == "S":
            position = (robot_r, robot_c)
            floor_ball = ball_at.get(position)
            if holding_ball is None:
                if floor_ball is not None:
                    holding_ball = floor_ball
                    del ball_at[position]
            else:
                if floor_ball is None:
                    ball_at[position] = holding_ball
                    holding_ball = None
                else:
                    ball_at[position] = holding_ball
                    holding_ball = floor_ball

    for command in commands:
        if executed_base_steps >= t_limit:
            break
        execute_command(command)

    success = sum(1 for idx, basket in enumerate(baskets) if ball_at.get(basket) == idx)
    score = len(commands) if success == m else t_limit * (m - success)
    return score, success, len(commands)


def build_env(params: SolverParams) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "SA_TIME_LIMIT": str(params.sa_time_limit),
            "SA_T_START": str(params.sa_t_start),
            "SA_T_END": str(params.sa_t_end),
            "SA_PROB_SWAP": str(params.sa_prob_swap),
            "SA_PROB_INSERT": str(params.sa_prob_insert),
        }
    )
    return env


def run_solver(script_dir: Path, input_text: str, params: SolverParams) -> list[str]:
    exe_path = script_dir / "main_optuna.exe"
    completed = subprocess.run(
        [str(exe_path)],
        input=input_text,
        text=True,
        capture_output=True,
        env=build_env(params),
        timeout=params.sa_time_limit + 5.0,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Solver failed: {completed.stderr}")
    return [line for line in completed.stdout.splitlines() if line]


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    input_texts = []
    for path_str in args.inputs:
        path = Path(path_str)
        if not path.is_absolute():
            path = script_dir / path
        if path.exists():
            input_texts.append((path.name, read_input_text(path)))
        else:
            print(f"Warning: {path} not found.")

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=args.seed))

    def objective(trial: optuna.Trial) -> float:
        params = SolverParams(
            sa_time_limit=1.9,  # 固定気味
            sa_t_start=trial.suggest_float("sa_t_start", 1.0, 100.0, log=True),
            sa_t_end=trial.suggest_float("sa_t_end", 0.001, 1.0, log=True),
            sa_prob_swap=trial.suggest_int("sa_prob_swap", 10, 80),
            sa_prob_insert=trial.suggest_int("sa_prob_insert", 10, 80),
        )

        # swap + insert が 100 を超えないように調整（あるいは C++ 側でよしなに）
        # ここでは単純に合計スコアを返す
        total_score = 0
        for name, text in input_texts:
            try:
                commands = run_solver(script_dir, text, params)
                score, success, _ = simulate_score(text, commands)
                total_score += score
            except Exception as e:
                return 1e18
        return total_score / len(input_texts)

    study.optimize(objective, n_trials=args.trials, timeout=args.timeout)
    print(f"Best value: {study.best_value}")
    print(f"Best params: {json.dumps(study.best_params, indent=2)}")


if __name__ == "__main__":
    main()
