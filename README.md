# 投信ドローダウン監視ダッシュボード（公開・配信用）

保有投資信託の「直近ピークからの下落率（ドローダウン）」を毎日可視化し、買い増しタイミングを見るための実験ツール。**このリポジトリは配信専用の公開リポジトリ**です。

- 公開ダッシュボード: GitHub Pages（Actions → Pages で自動公開）
- 毎営業日の朝(JST 07:00)にクラウドで自動更新。PC常時起動は不要。

## 公開しているもの／していないもの
- ✅ 公開: 保有銘柄名・ドローダウン率(%)・公開データである基準価額(`history.json`)
- 🔒 非公開: **評価額(金額)は一切置いていない**。口座別DDの加重計算に使う金額は GitHub Secret `WEIGHTS`（JSON: `wkey`→円）から実行時に注入し、出力HTMLには%しか出さない。

## ファイル
| ファイル | 役割 |
|---|---|
| `config.json` | 銘柄マスタ（協会コード・ISIN・wkey。**金額なし**） |
| `dd_lib.py` | 取得＆DD計算の共通ロジック |
| `backfill.py` | 設定来履歴の取り込み（初回のみ・公募6本） |
| `fetch_nav.py` | 日次の当日基準価額取得 |
| `generate_html.py` | HTML生成（金額はenv `WEIGHTS`から） |
| `template.html` / `dashboard.html` | 雛形／出力 |
| `history.json` | 蓄積された基準価額（公開データ） |

## セットアップ（済み）
1. リポジトリ Settings → Pages → Source: **GitHub Actions**
2. Settings → Actions → General → Workflow permissions: **Read and write**
3. Secret `WEIGHTS` に評価額のJSONを登録（`gh secret set WEIGHTS`）
4. Actions → `update-dashboard` → Run workflow で初回公開

## データ入手の前提
- 当日基準価額: Yahoo!ファイナンス（`finance.yahoo.co.jp/quote/{協会コード}` の埋め込みJSON）。
- 設定来バックフィル: 投信ライブラリー（`toushin-lib.fwg.ne.jp`）CSV。ISIN必須（公募6本のみ）。
- DC専用8本はISIN未公開 → 稼働日から前方蓄積。
- 基準価額は翌営業日確定のため実質1営業日遅れ。

## 次段階
- 資産クラス代表指数（円ベース, MSCIコクサイ/S&P500）の実データ接続。
- DC内2本（三菱UFJスリム全世界／ニッセイJリート）の正式コード確定。
