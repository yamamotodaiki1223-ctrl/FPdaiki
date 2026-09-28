# 経済・お金ニュース LINE Bot

信頼度の高い大手メディアから、経済・お金に関わる記事を1日1回LINEに配信します。
GitHub Actionsで毎朝7:00(JST)に自動実行されます。

## 配信元

**Yahoo!ニュース(経済)** — 経済カテゴリの記事をそのまま配信(重要な大きめのトピック向け)

**Google News検索(2系統)** — 以下の信頼できる大手メディアのドメインに限定して、キーワード検索で横断的に拾う

- 対象ドメイン: NHK、日本経済新聞、ロイター、時事通信、朝日新聞、読売新聞、毎日新聞、共同通信、東洋経済オンライン、ダイヤモンド・オンライン
- 系統1「経済・政策ニュース」: 物価・金利・日銀・税制・社会保険・年金など、マクロ経済の重要トピック
- 系統2「家計・お金ニュース」: NISA・iDeCo・保険・住宅ローン・児童手当・相続・教育費など、FPの活動に直結する個人のお金の細かい話題

`site:ドメイン`指定でGoogle News検索を絞り込んでいるため、各メディア個別にRSSを取得できない・信頼性が不明という問題を避けつつ、大手メディアの記事だけに限定しています。

キーワードは [fetch_news.py](fetch_news.py) 内の `MACRO_KEYWORDS` / `PERSONAL_FINANCE_KEYWORDS`、対象メディアは `TRUSTED_DOMAINS` で調整できます。
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
- **キーワードを調整する**: `fetch_news.py` の `MACRO_KEYWORDS` / `PERSONAL_FINANCE_KEYWORDS` を編集
- **対象メディアを増減する**: 同ファイルの `TRUSTED_DOMAINS` を編集
- **1通あたりの記事数**: `MAX_ARTICLES`(デフォルト15件)
