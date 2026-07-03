import argparse
from atro.core import init_contest


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("contest_name")
    parser.add_argument("-c", "--contest", choices=["ahc", "abc"], default=None, help="コンテスト種別。(abc または ahc)略した場合はコンテスト名から自動判別します。")

    parser.add_argument("-o", "--objective", choices=["max", "min"], help="スコアが大きいほど良いか、小さいほど良いか。")
    parser.add_argument("-l", "--language", choices=["cpp", "python", "rust"], required=True, help="使用する言語。")
    parser.add_argument("-i", "--interactive", action="store_true", help="インタラクティブ問題の場合に使用する。")
    parser.add_argument("-u", "--tools-url", help="ローカルツール（インプットジェネレータ・テスタ）のZIPダウンロードURL。(AHC用)")

    args = parser.parse_args()

    # コンテスト種別の自動判別
    contest_type = args.contest
    if not contest_type:
        contest_name_lower = args.contest_name.lower()
        if "abc" in contest_name_lower:
            contest_type = "abc"
        elif "ahc" in contest_name_lower:
            contest_type = "ahc"
        else:
            parser.error("コンテスト名から種別を自動判別できませんでした。-c/--contest 引数で abc または ahc を明示してください。")

    # AHCの場合はobjective（max/min）が必須
    if contest_type == "ahc" and not args.objective:
        parser.error("AHCコンテストでは、目的関数の指定（-o/--objective {max,min}）が必須です。")

    init_contest(
        contest_type=contest_type,
        contest_name=args.contest_name,
        objective=args.objective,
        language=args.language,
        interactive=args.interactive,
        tools_url=args.tools_url,
    )
