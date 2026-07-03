## 自動構築

自動構築スクリプトを使うことで、AHC,ABCの構築を自動で行います。

```bash
# AHC
atro ahc067 -l cpp -u https://img.atcoder.jp/ahc067/BpPfrS30.zip -o max
atro 067 -c ahc -l cpp -u https://img.atcoder.jp/ahc067/BpPfrS30.zip -o max

# ABC
atro abc123 -l python
atro 123 -c abc -l python
```

- `ahc067`: 067と指定することも可能です。その場合は、`-c ahc`と指定します。
- `-c, --contest`: コンテスト種別。(abc, ahc)省略した場合、コンテスト名から自動判断します。
- `-l, --language`: 使用する言語。(cpp, python, rust)

以下はAHC限定機能です。
- `-o, --objective`: 点数が高いほどいいか、低いほどいいか。(max, min)
- `-i, --interactive`: インタラクティブ問題である場合につける。
- `-u, --tools-url`: ローカルテストツール(Rustバージョン)のZIPダウンロードURLを指定すると、自動で配置される。

なお、自動構築では `devtools/pahcer-studio` をそのままリンクせず、必要なファイルだけをコピーしてからビルドします。初回は少し待ち時間があります。

## Pahcer

AHCでは、Pahcer、PahcerStudioを利用して、テストケースを実行します。
> https://blog.terry-u16.net/entry/how-to-use-pahcer

<details>
<summary>参考: 手動Pahcerの使い方</summary>

このリポジトリでは、PahcerはMiseでインストールされます。PahcerStudioは、個別にGitからクローンする必要があります。
自動構築では、コピー後に `pnpm install` と `pnpm build` を実行するため、完了までしばらく待ってください。

1. ファイルを配置

```
your-ahc-project/
├── main.cpp             # 開発したプログラム、言語は好みで選択してください
├── pahcer_config.toml    # pahcer の設定ファイル
├── tools/                # AHCから配布される tools フォルダ
│   ├── in/              # 入力ファイル
│   └── out/             # 出力ファイル
└── pahcer-studio/       # このリポジトリをクローンする場所
    ├── src/
    ├── package.json
    └── ...
```

toolsは、Rustで書かれたものが必要です。

2. pahcerプロジェクトの初期化

```bash
pahcer init -p <PROBLEM_NAME> -o <OBJECTIVE> -l <LANGUAGE> [-i]
```
オプション:
- <PROBLEM_NAME> : コンテスト名
- <OBJECTIVE> : スコアを最大化するか最小化するか
  - max : スコアが大きいほど良い
  - min : スコアが小さいほど良い
- <LANGUAGE> : 開発言語
  - cpp : C++
  - rust : Rust
  - python : Python
- -i : インラタクティブ問題かどうか

コマンド例
```bash
pahcer init -p ahc039 -o max -l cpp
pahcer init -p ahc030 -o min -l python -i
```

3. pahcer-studio のクローン

AHCプロジェクトディレクトリ内で、PahcerStudioをクローンします。

```bash
git clone https://github.com/yunix-kyopro/pahcer-studio.git
cd pahcer-studio
rm -rf .git

pnpm import  # yarnからpnpmへ変更する。
pnpm install
```

install後、package.jsonのscripts内で、yarn依存をpnpmに変更してください。

4. pahcer-studio の起動

```bash
pnpm run start
```

</details>

## Tool Setup

このリポジトリでは、以下のツールが必要です。

- rust
- uv, python
- mise
- C++実行環境 (gcc)
- node.js, pnpm

環境構築、パスを通した後、以下のコマンドで、必要なツールをインストールします。
> mise は、アクティベーションする必要があります。

```bash
cargo install cargo-binstall
mise install
uv sync
uv venv
pahcer --version
```
