import subprocess
import sys
from pathlib import Path
import os

# tune_op_algo.py からインポートを試みる（パスの問題がある場合は直接定義する）
# ここでは確実性のために、必要なロジックを再定義するか、tune_op_algo.py を読み込む
sys.path.append(str(Path(__file__).parent))
import tune_op_algo


def run_solver(script_name, input_text, env=None):
    completed = subprocess.run(
        [sys.executable, script_name],
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        timeout=10.0,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return [line for line in completed.stdout.splitlines() if line]


def main():
    script_dir = Path(__file__).parent
    inputs = [script_dir / "in" / f"{i:04d}.txt" for i in range(10)]
    solvers = ["main.py", "algo.py", "op_algo.py"]

    # op_algo.py 用のベストパラメータ
    best_params = {
        "OP_TIME_LIMIT": "1.6246106644274163",
        "OP_RANDOM_SEED": "42",
        "OP_BEAM_WIDTH_EARLY": "170",
        "OP_BEAM_WIDTH_MID": "60",
        "OP_BEAM_WIDTH_LATE": "90",
        "OP_BEAM_THRESHOLD_1": "16",
        "OP_BEAM_THRESHOLD_2": "80",
        "OP_CANDIDATE_LIMIT": "8",
        "OP_ROLLOUT_K_SHORT": "1",
        "OP_ROLLOUT_K_LONG": "4",
        "OP_ROLLOUT_PROB_LONG": "0.019413361686626718",
        "OP_MACRO_MIN_COUNT": "2",
    }

    results = {s: [] for s in solvers}

    print(f"{'Input':<12} | {'main.py':<10} | {'algo.py':<10} | {'op_algo.py':<10}")
    print("-" * 55)

    for input_path in inputs:
        input_text = input_path.read_text(encoding="utf-8")
        row = [input_path.name]
        for s in solvers:
            env = os.environ.copy()
            if s == "op_algo.py":
                env.update(best_params)

            commands = run_solver(script_dir / s, input_text, env=env)
            if commands is None:
                score = float("inf")
            else:
                score, success, cmd_count = tune_op_algo.simulate_score(input_text, commands)

            results[s].append(score)
            row.append(f"{score:10.1f}")

        print(f"{row[0]:<12} | {row[1]:<10} | {row[2]:<10} | {row[3]:<10}")

    print("-" * 55)
    print(f"{'Average':<12}", end=" | ")
    for s in solvers:
        avg = sum(results[s]) / len(results[s])
        print(f"{avg:10.1f}", end=" | ")
    print()


if __name__ == "__main__":
    main()
