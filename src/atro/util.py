from importlib import resources
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
import io


def get_project_root() -> Path:
    # NOTE: グローバルツールとして実行された場合でもプロジェクトルートを特定できるように、.git や pyproject.toml を探します
    current = Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return current


def create_main(contest_dir: Path, language: str):
    filename = "main.cpp" if language == "cpp" else "main.py"
    lang_dir = "cpp" if language == "cpp" else "python"

    # NOTE: AHC用のテンプレートを参照します
    template_path = resources.files("initer") / "templates" / "ahc" / lang_dir / filename

    with template_path.open("rb") as f:
        (contest_dir / filename).write_bytes(f.read())


def copy_pahcer_studio(contest_dir: Path):
    root = get_project_root()
    source = root / "devtools" / "pahcer-studio"
    target = contest_dir / "pahcer-studio"

    if target.exists():
        if target.is_symlink():
            target.unlink()
        else:
            return

    def ignore_patterns(_dir, names):
        ignored = {"dist", "node_modules"}
        return [name for name in names if name in ignored]

    shutil.copytree(source, target, ignore=ignore_patterns)


def run_command_with_spinner(command, cwd: Path, message: str):
    print(message)
    print(f"  実行中: {' '.join(command)}")

    process = subprocess.Popen(command, cwd=cwd)

    start = time.monotonic()
    shown = False

    # メッセージから処理中の文言を生成 (例: "インストールしています。" -> "インストール中")
    progress_name = message.replace("少しお待ちください", "").strip("。 ")
    if progress_name.endswith("しています"):
        progress_name = progress_name[:-5] + "中"
    elif progress_name.endswith("しています。"):
        progress_name = progress_name[:-6] + "中"

    if not progress_name:
        progress_name = "処理中"

    while process.poll() is None:
        elapsed = int(time.monotonic() - start)

        if elapsed >= 30:
            print(f"\r  {progress_name}...（{elapsed}秒経過)", end="", flush=True)
            shown = True

        time.sleep(1)

    if shown:
        print()

    print("  完了しました。")

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)


def build_pahcer_studio(studio_dir: Path):
    node_modules = studio_dir / "node_modules"
    if not node_modules.exists():
        run_command_with_spinner(
            ["pnpm", "install"],
            cwd=studio_dir,
            message="pahcer-studio の依存関係をインストールしています。",
        )

    run_command_with_spinner(
        ["pnpm", "start"],
        cwd=studio_dir,
        message="pahcer-studio を起動しています。少しお待ちください。",
    )


def download_and_extract_tools(url: str, tools_dir: Path):
    # クエリパラメータなどを除去してURLを整形
    url = url.split("?")[0].strip()

    print(f"Downloading tools from: {url}...")

    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            zip_data = response.read()
    except Exception as e:
        print(f"Error: Failed to download tools from {url}. Reason: {e}")
        return

    print(f"Extracting tools to {tools_dir}...")
    try:
        tools_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            # NOTE: ZIPのトップレベルにフォルダが1つだけある場合（例: tools/）は、
            # そのフォルダを剥がして tools_dir 直下に展開します。
            # 例: zip内の tools/in/0001.txt → tools_dir/in/0001.txt
            entries = zip_ref.namelist()
            top_level = {e.split("/")[0] for e in entries if e}
            prefix = ""
            if len(top_level) == 1:
                candidate = next(iter(top_level))
                # トップレベルがディレクトリである（名前だけのエントリが存在する）か確認
                if (candidate + "/") in entries or any(e.startswith(candidate + "/") for e in entries):
                    prefix = candidate + "/"

            for member in zip_ref.infolist():
                name = member.filename
                if prefix and name.startswith(prefix):
                    # プレフィックスを除去したパスで展開先を決定
                    relative = name[len(prefix):]
                    if not relative:
                        # トップレベルフォルダ自体はスキップ
                        continue
                    dest = tools_dir / relative
                    if member.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(zip_ref.read(member.filename))
                elif not prefix:
                    # トップレベルフォルダが存在しない場合はそのまま展開
                    zip_ref.extract(member, tools_dir)

        print("Tools successfully extracted!")
    except Exception as e:
        print(f"Error: Failed to extract zip file. Reason: {e}")
