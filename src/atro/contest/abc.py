from importlib import resources
from atro.util import get_project_root

ROOT = get_project_root()


def init_abc(name, language):
    contest_dir = ROOT / "ABC" / name
    contest_dir.mkdir(parents=True, exist_ok=True)

    # 拡張子とテンプレートの設定
    if language == "cpp":
        ext = "cpp"
        lang_dir = "cpp"
        template_filename = "main.cpp"
    elif language == "python":
        ext = "py"
        lang_dir = "python"
        template_filename = "main.py"
    else:
        ext = "rs"
        lang_dir = "rust"
        template_filename = "main.rs"

    # NOTE: ABC用のテンプレートを参照します
    template_path = resources.files("initer") / "templates" / "abc" / lang_dir / template_filename

    # テンプレートが存在すれば読み込む
    # importlib.resources.Traversable provides is_file(), not exists()
    if template_path.is_file():
        with template_path.open("rb") as f:
            template_content = f.read()
    else:
        template_content = b""

    # AからG問題までのファイルを作成
    for problem in ["A", "B", "C", "D", "E", "F", "G"]:
        problem_file = contest_dir / f"{problem}.{ext}"
        if not problem_file.exists():
            problem_file.write_bytes(template_content)
