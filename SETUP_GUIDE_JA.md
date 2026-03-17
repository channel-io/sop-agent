# セットアップガイド

ExcelのカスタマーサポートデータをAgent SOPドキュメント＋フローチャートに自動変換するAIパイプラインのセットアップガイドです。

---

## 事前準備

1. **Claude Code のインストール** — https://claude.ai/code
2. **Upstage APIキーの取得** — DMにてお送りします！

---

## インストール方法

### 方法 1. ターミナルから直接インストール

```bash
# 1. セットアップスクリプトを実行 (Python仮想環境＋パッケージを自動インストール)
chmod +x setup.sh
./setup.sh

# 2. APIキーを入力
# .env ファイルに UPSTAGE_API_KEY を記入
```

### 方法 2. Claude Code にインストールを依頼 (ターミナル不要)

1. このフォルダを Claude Code で開く
2. チャット欄に以下のメッセージをそのまま貼り付ける:

```
setup.sh を見て環境設定をしてください。また .env.example をコピーして .env ファイルを作成し、UPSTAGE_API_KEY の入力場所を案内してください。
```

3. Claude Code が自動でインストールを進め、APIキーの入力場所を案内します。

---

## 実行方法

`data/` フォルダにカスタマーサポートのExcelファイルを入れ、そのフォルダを Claude Code で開いてコマンドを実行:

```
/userchat-to-sop-pipeline    # SOPドキュメント＋フローチャート生成 (約15〜30分)
```

> **日本語モードで実行する場合:** スキルを起動すると最初に言語選択を求められます。「日本語」を選択してください。Python スクリプトには自動的に `LANGUAGE=ja` が適用されます。

ステージごとに実行する場合:

```
/stage1-clustering              # クラスタリング
/stage2-extraction              # パターン抽出
/stage3-sop-generation          # SOPドキュメント生成
/stage4-flowchart-generation    # フローチャート生成
/stage5-sop-to-guide            # ALF構築パッケージ生成
```

---

## トラブルシューティング

### "pip3: command not found"

```bash
python3 -m ensurepip --upgrade
```

### "Permission denied" または "Externally managed environment"

```bash
# 仮想環境を使用 (推奨)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "ImportError: No module named 'pandas'"

```bash
pip3 install pandas numpy scikit-learn openpyxl openai tqdm --user
```

### その他のエラー

エラーメッセージを Claude Code に貼り付けると、自動で解決策を提示します。

---

## Stage 4 フローチャート SVG 生成 (オプション)

Mermaid CLI がなくてもマークダウンファイルは生成されます。SVG画像が必要な場合のみインストールしてください。

```bash
# Node.js インストール確認
node --version

# Mermaid CLI インストール
npm install -g @mermaid-js/mermaid-cli

# SVG変換
mmdc -i FLOWCHART.md -o flowchart.svg -b transparent
```
