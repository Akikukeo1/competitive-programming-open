from pathlib import Path
from atro.pahcer import run_pahcer
from atro.util import create_main, get_project_root, download_and_extract_tools, copy_pahcer_studio, build_pahcer_studio


ROOT = get_project_root()


def init_ahc(name, objective, language, interactive, tools_url=None):
    contest_dir = ROOT / "AHC" / name
    contest_dir.mkdir(parents=True, exist_ok=True)

    (contest_dir / "tools" / "in").mkdir(parents=True, exist_ok=True)
    (contest_dir / "tools" / "out").mkdir(parents=True, exist_ok=True)

    create_main(contest_dir, language)

    if tools_url:
        download_and_extract_tools(tools_url, contest_dir / "tools")

    run_pahcer(name, objective, language, interactive, contest_dir)
    copy_pahcer_studio(contest_dir)
    build_pahcer_studio(contest_dir / "pahcer-studio")
    print("AHCコンテストが正常に作成されました。")
