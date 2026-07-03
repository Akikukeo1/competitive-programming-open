from pathlib import Path


def link_studio(contest_dir: Path):
    root = contest_dir.parents[1]

    target = root / "devtools" / "pahcer-studio"
    link = contest_dir / "pahcer-studio"

    if link.exists():
        return

    link.symlink_to(target, target_is_directory=True)
