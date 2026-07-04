from __future__ import annotations

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
    time_limit: float = 1.75
    random_seed: int = 42
    beam_width_early: int = 100
    beam_width_mid: int = 70
    beam_width_late: int = 40
    beam_threshold_1: int = 33
    beam_threshold_2: int = 66
    candidate_limit: int = 5
    rollout_short_k: int = 2
    rollout_long_k: int = 3
    rollout_long_prob: float = 0.1
    macro_min_count: int = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="op_algo.py のパラメータを Optuna で探索する")
    parser.add_argument(
        "inputs",
        nargs="*",
        default=["input.txt"],
        help="評価に使う入力ファイル。省略時は現在ディレクトリの input.txt",
    )
    parser.add_argument("--trials", type=int, default=50, help="Optuna の試行回数")
    parser.add_argument("--timeout", type=float, default=None, help="Optuna 全体の制限時間（秒）")
    parser.add_argument("--seed", type=int, default=42, help="Optuna の乱数シード")
    parser.add_argument("--study-name", default="op_algo_tuning", help="保存用の study 名")
    parser.add_argument("--storage", default=None, help="SQLite などの永続ストレージ URI")
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
        raise ValueError("不正な方向です")

    robot_r = 0
    robot_c = 0
    robot_dir = 1
    holding_ball = None
    ball_at = {pos: idx for idx, pos in enumerate(balls)}

    registered_macro: list[str] = []
    recording = False
    recording_buffer: list[str] = []
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
            return

        if command == "R":
            robot_dir = (robot_dir + 1) % 4
            return

        if command == "L":
            robot_dir = (robot_dir - 1) % 4
            return

        if command == "S":
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
            return

        raise ValueError(f"未知コマンド: {command}")

    for command in commands:
        if executed_base_steps >= t_limit:
            break
        execute_command(command)

    success = sum(1 for idx, basket in enumerate(baskets) if ball_at.get(basket) == idx)
    if success == m:
        score = len(commands)
    else:
        score = t_limit * (m - success)

    return score, success, len(commands)


def build_env(params: SolverParams) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "OP_TIME_LIMIT": str(params.time_limit),
            "OP_RANDOM_SEED": str(params.random_seed),
            "OP_BEAM_WIDTH_EARLY": str(params.beam_width_early),
            "OP_BEAM_WIDTH_MID": str(params.beam_width_mid),
            "OP_BEAM_WIDTH_LATE": str(params.beam_width_late),
            "OP_BEAM_THRESHOLD_1": str(params.beam_threshold_1),
            "OP_BEAM_THRESHOLD_2": str(params.beam_threshold_2),
            "OP_CANDIDATE_LIMIT": str(params.candidate_limit),
            "OP_ROLLOUT_K_SHORT": str(params.rollout_short_k),
            "OP_ROLLOUT_K_LONG": str(params.rollout_long_k),
            "OP_ROLLOUT_PROB_LONG": str(params.rollout_long_prob),
            "OP_MACRO_MIN_COUNT": str(params.macro_min_count),
        }
    )
    return env


def run_solver(script_dir: Path, input_text: str, params: SolverParams) -> list[str]:
    completed = subprocess.run(
        [sys.executable, "op_algo.py"],
        cwd=script_dir,
        input=input_text,
        text=True,
        capture_output=True,
        env=build_env(params),
        timeout=max(10.0, params.time_limit + 8.0),
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(f"solver 実行に失敗しました\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")

    return [line for line in completed.stdout.splitlines() if line]


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    input_paths = [Path(arg) for arg in args.inputs]
    input_texts = []
    for path in input_paths:
        candidate = path if path.is_absolute() else path
        if not candidate.exists() and not candidate.is_absolute():
            candidate = script_dir / path
        input_texts.append((candidate, read_input_text(candidate)))

    sampler = optuna.samplers.TPESampler(seed=args.seed)
    study = optuna.create_study(
        direction="minimize",
        study_name=args.study_name,
        sampler=sampler,
        storage=args.storage,
        load_if_exists=bool(args.storage),
    )

    def objective(trial: optuna.Trial) -> float:
        params = SolverParams(
            time_limit=trial.suggest_float("time_limit", 1.4, 1.9),
            random_seed=args.seed,
            beam_width_early=trial.suggest_int("beam_width_early", 40, 180, step=10),
            beam_width_mid=trial.suggest_int("beam_width_mid", 20, 140, step=10),
            beam_width_late=trial.suggest_int("beam_width_late", 10, 100, step=10),
            beam_threshold_1=trial.suggest_int("beam_threshold_1", 8, 50),
            beam_threshold_2=trial.suggest_int("beam_threshold_2", 20, 90),
            candidate_limit=trial.suggest_int("candidate_limit", 3, 10),
            rollout_short_k=trial.suggest_int("rollout_short_k", 1, 3),
            rollout_long_k=trial.suggest_int("rollout_long_k", 2, 5),
            rollout_long_prob=trial.suggest_float("rollout_long_prob", 0.0, 0.4),
            macro_min_count=trial.suggest_int("macro_min_count", 1, 3),
        )

        if params.beam_threshold_1 > params.beam_threshold_2:
            params = SolverParams(
                **{
                    **asdict(params),
                    "beam_threshold_1": params.beam_threshold_2,
                    "beam_threshold_2": params.beam_threshold_1,
                }
            )

        total_score = 0.0
        for input_path, input_text in input_texts:
            try:
                commands = run_solver(script_dir, input_text, params)
                score, success, command_count = simulate_score(input_text, commands)
            except Exception as exc:  # noqa: BLE001
                trial.set_user_attr("failed_input", str(input_path))
                trial.set_user_attr("failure_reason", str(exc))
                return 10**18

            total_score += score
            trial.set_user_attr(f"{input_path.name}_success", success)
            trial.set_user_attr(f"{input_path.name}_commands", command_count)

        return total_score

    study.optimize(objective, n_trials=args.trials, timeout=args.timeout)

    print(f"best_value: {study.best_value}")
    print(json.dumps(asdict(SolverParams(**study.best_params, random_seed=args.seed)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
