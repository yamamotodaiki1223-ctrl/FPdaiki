# 教育・子育てお金ニュース LINE Bot

教育・出産・子育て系ニュースサイトから、お金に関わる記事だけを1日1回LINEに配信します。
GitHub Actionsで毎朝7:00(JST)に自動実行されます。

## 配信元サイト

**教育・子育て専門サイト**(「お金」キーワードで絞り込み)
- リセマム
- こどもまなび☆ラボ

**お金専門サイト**(「子育て・教育」キーワードで絞り込み)
- ファイナンシャルフィールド
- マネーの達人

**一般ニュース**(「お金」キーワードで絞り込み)
- Yahoo!ニュース(経済)※お金キーワードの代わりに子育て・教育キーワードで絞り込み
- Yahoo!ニュース(国内)

**一般ニュース横断検索**(検索クエリ自体で「お金×子育て/教育」に絞り込み済み)
- Google News(児童手当・学資保険・保育料など複合キーワード検索、直近1日以内)

Google News検索により、NHK・読売・朝日・地方紙・専門メディアなど個別にRSSを持たない/取得できないサイトの記事も横断的に拾えます。
キーワードは [fetch_news.py](fetch_news.py) 内の `MONEY_KEYWORDS` / `CHILD_EDU_KEYWORDS`、Google Newsの検索クエリは `SOURCES` 内の `url` で調整できます。
同じ記事が複数ソースに出た場合はリンク・タイトルで重複除去しています。

## セットアップ手順

### 1. LINE公式アカウントを作る

1. https://www.linebiz.com/jp/entry/ から「LINE公式アカウント」を無料開設(既存のLINEアカウントでログイン可)
2. 開設後、[LINE Official Account Manager](https://manager.line.biz/) にログイン
3. 「設定」→「Messaging API」→「Messaging APIを利用する」を有効化
4. 表示される「チャネルアクセストークン」の発行ボタンを押し、トークンをコピーして控えておく(後でGitHubに登録します)
5. 自分のスマホのLINEアプリで、このアカウントを友だち追加しておく(Broadcast配信は「友だち」にのみ届くため必須)
6. 応答モードは「応答なし」にしておくとよい(Bot管理画面の「応答設定」)

無料プランは月200通まで無料。1日1通なので余裕で収まります。

### 2. GitHubリポジトリを作る

1. https://github.com/new で新規リポジトリを作成(Private推奨)
2. 「uploading an existing file」リンク、または作成後の「Add file」→「Upload files」から、このフォルダ内の以下をすべてアップロード
   - `fetch_news.py`
   - `requirements.txt`
   - `.github/workflows/daily_news.yml`(フォルダ構造ごと)
   - このREADME.md

   ※ `.github/workflows/daily_news.yml` は、アップロード画面にフォルダごとドラッグ&ドロップすればパスを保ったまま登録されます。

### 3. トークンをGitHub Secretsに登録

1. リポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」
   - Name: `LINE_CHANNEL_ACCESS_TOKEN`
   - Secret: 手順1でコピーしたチャネルアクセストークン
3. 保存

### 4. 動作確認

1. リポジトリの「Actions」タブ→「Daily News to LINE」を選択
2. 「Run workflow」で手動実行
3. 数十秒後、LINEに通知が届けば成功(該当記事がない日は配信されずログのみ)

以降は毎朝7:00(JST)に自動実行されます。

## カスタマイズ

- **配信時刻を変える**: `.github/workflows/daily_news.yml` の `cron` を変更(UTC指定。JST = UTC+9)
- **ニュースソースを増減する**: `fetch_news.py` の `SOURCES` リストを編集
- **キーワードを調整する**: 同ファイルの `MONEY_KEYWORDS` / `CHILD_EDU_KEYWORDS` を編集
- **1通あたりの記事数**: `MAX_ARTICLES`(デフォルト10件)
