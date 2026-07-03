import subprocess
from pathlib import Path


def run_pahcer(problem_name: str, objective: str, language: str, interactive: bool, contest_dir: Path):
    cmd = [
        "pahcer",
        "init",
        "-p", problem_name,
        "-o", objective,
        "-l", language,
    ]

    if interactive:
        cmd.append("-i")

    subprocess.run(cmd, cwd=contest_dir, check=True)

    config_path = contest_dir / "pahcer_config.toml"
    config_path.touch(exist_ok=True)
