AWS生成AI API構成の確認項目

1. プロジェクト全体

* [ ]	想定ユーザー数
* [ ]	最大同時利用者数
* [ ]	1日あたりのAPI呼び出し回数
* [ ]	ピーク時間帯
* [ ]	生成AI処理の平均時間
* [ ]	生成AI処理の最大時間
* [ ]	生成AI処理の p95 / p99
* [ ]	30秒を超える処理があるか
* [ ]	最大で何分程度かかる可能性があるか
* [ ]	同期レスポンスが必須か
* [ ]	ストリーミングレスポンスで問題ないか
* [ ]	非同期処理でも問題ないか
* [ ]	APIは社内限定か、外部公開か
* [ ]	必要な可用性
* [ ]	障害時にどこまで許容できるか
* [ ]	月額コスト上限
* [ ]	個人情報・機密情報を扱うか
* [ ]	入力内容・生成結果をログに残してよいか
* [ ]	利用リージョンに制約があるか
* [ ]	今後APIがどの程度増える予定か

⸻

2. API Gateway

API種別

* [ ]	HTTP APIで要件を満たせるか
* [ ]	REST APIが必要か
* [ ]	30秒以上の処理が発生するか
* [ ]	Response Streamingが必要か

認証・認可

* [ ]	JWT Authorizerを利用するか
* [ ]	Lambda Authorizerを利用するか
* [ ]	Cognitoを利用するか
* [ ]	外部IdPを利用するか
* [ ]	API Keyが必要か
* [ ]	Usage Planが必要か

公開・制御

* [ ]	WAFが必要か
* [ ]	IP制限が必要か
* [ ]	Rate Limitが必要か
* [ ]	ユーザー単位のRate Limitが必要か
* [ ]	カスタムドメインが必要か
* [ ]	CORS設定が必要か

制限・ログ

* [ ]	最大リクエストサイズ
* [ ]	最大レスポンスサイズ
* [ ]	アクセスログを有効にするか
* [ ]	dev / stg / prod でステージを分けるか
* [ ]	API Gatewayのタイムアウト値を確認する

⸻

3. Lambda

基本設定

* [ ]	Runtime
* [ ]	Pythonバージョン
* [ ]	メモリサイズ
* [ ]	タイムアウト値
* [ ]	/tmp の必要容量
* [ ]	Lambdaを1つにまとめるか
* [ ]	機能ごとにLambdaを分割するか

起動方式・性能

* [ ]	コールドスタート時間を計測する
* [ ]	ウォーム時の実行時間を計測する
* [ ]	コールドスタートによる遅延が許容できるか
* [ ]	On-demandで問題ないか
* [ ]	SnapStartを利用するか
* [ ]	Provisioned Concurrencyを利用するか
* [ ]	Reserved Concurrencyを設定するか
* [ ]	最大同時実行数を制限する必要があるか

ネットワーク・デプロイ

* [ ]	VPCに入れる必要があるか
* [ ]	RDSなどVPC内リソースへアクセスするか
* [ ]	Lambda Layerを利用するか
* [ ]	ZIPデプロイで十分か
* [ ]	コンテナイメージを利用するか

設定情報

* [ ]	環境変数に何を設定するか
* [ ]	Secrets Managerを利用するか
* [ ]	Parameter Storeを利用するか
* [ ]	秘密情報を環境変数へ直接保存していないか

⸻

4. FastAPI

* [ ]	APIルート一覧を整理する
* [ ]	/token
* [ ]	/bedrock
* [ ]	今後追加予定のAPI
* [ ]	Request schemaを定義する
* [ ]	Response schemaを定義する
* [ ]	Pydanticによる入力チェックを利用する
* [ ]	共通エラー処理を実装する
* [ ]	エラーレスポンス形式を統一する
* [ ]	ロギング方式を決める
* [ ]	OpenAPIを利用するか
* [ ]	Swagger UIを外部公開するか
* [ ]	Mangumを利用するか
* [ ]	Response Streaming時にMangumで対応可能か確認する
* [ ]	FastAPI起動時に重い初期化処理がないか
* [ ]	boto3クライアントなどを毎回生成していないか

⸻

5. Amazon Bedrock

モデル

* [ ]	使用するモデル
* [ ]	モデルID
* [ ]	利用リージョン
* [ ]	Inference Profileを利用するか

性能

* [ ]	平均レスポンス時間
* [ ]	最大レスポンス時間
* [ ]	p95 / p99
* [ ]	30秒を超えるケースがあるか
* [ ]	最大入力トークン数
* [ ]	最大出力トークン数
* [ ]	通常の入力トークン数
* [ ]	通常の出力トークン数

API

* [ ]	Converse APIを利用するか
* [ ]	InvokeModelを利用するか
* [ ]	InvokeModelWithResponseStreamを利用するか
* [ ]	利用モデルがStreamingに対応しているか

制限・障害対応

* [ ]	Requests per minuteのQuota
* [ ]	Tokens per minuteのQuota
* [ ]	Throttling時の処理
* [ ]	リトライ回数
* [ ]	リトライ間隔
* [ ]	モデル障害時のフォールバックが必要か
* [ ]	Guardrailsを利用するか

コスト

* [ ]	1リクエストあたりの概算コスト
* [ ]	月間想定コスト
* [ ]	想定外の大量利用への対策
* [ ]	ユーザー単位の利用上限が必要か

⸻

6. JWT / 認証

* [ ]	JWTを誰が発行するか
* [ ]	Cognitoを利用するか
* [ ]	自前Lambdaで発行するか
* [ ]	外部IdPを利用するか
* [ ]	JWT有効期限
* [ ]	Refresh Tokenが必要か
* [ ]	JWT署名方式
* [ ]	秘密鍵 / 公開鍵の管理方法
* [ ]	issuerを検証するか
* [ ]	audienceを検証するか
* [ ]	scopeを利用するか
* [ ]	role / claimを利用するか
* [ ]	API Gateway側でJWTを検証するか
* [ ]	FastAPI側でJWTを検証するか
* [ ]	/token API自体をどう認証するか
* [ ]	誰でもJWTを取得できる状態になっていないか

⸻

7. IAM

人間用ロール

* [ ]	開発者が使用するロール
* [ ]	Lambda作成・更新権限
* [ ]	API Gateway作成・更新権限
* [ ]	必要な iam:PassRole
* [ ]	PassRole対象を必要なLambda実行ロールだけに限定する

Lambda実行ロール

* [ ]	CloudWatch Logs権限
* [ ]	bedrock:InvokeModel
* [ ]	bedrock:InvokeModelWithResponseStream
* [ ]	BedrockのResourceを必要なモデルだけに絞れるか
* [ ]	Secrets Manager利用権限
* [ ]	Parameter Store利用権限
* [ ]	S3利用時の権限
* [ ]	DynamoDB利用時の権限
* [ ]	最小権限になっているか

⸻

8. 外部公開APIとしてのセキュリティ

* [ ]	HTTPSのみ許可する
* [ ]	カスタムドメイン
* [ ]	WAF
* [ ]	Rate Limit
* [ ]	API Key
* [ ]	JWT
* [ ]	IP制限
* [ ]	リクエストサイズ制限
* [ ]	不正リクエストへの対策
* [ ]	Bedrockへの大量リクエスト対策
* [ ]	ユーザー単位の呼び出し回数制限
* [ ]	ユーザー単位のトークン使用量制限
* [ ]	AWS Budgetsなどによるコスト監視

⸻

9. 監視・ログ

API Gateway

* [ ]	Access Logs
* [ ]	4xx件数
* [ ]	5xx件数
* [ ]	レスポンスタイム

Lambda

* [ ]	Invocations
* [ ]	Errors
* [ ]	Duration
* [ ]	Init Duration
* [ ]	Throttles
* [ ]	ConcurrentExecutions
* [ ]	Timeouts

Bedrock

* [ ]	Bedrock呼び出し時間
* [ ]	Bedrockエラー数
* [ ]	Throttling件数
* [ ]	入力トークン数
* [ ]	出力トークン数
* [ ]	モデル別の利用量

アプリケーションログ

以下の時刻を取得できるようにする。

* [ ]	API受付時刻
* [ ]	Lambda開始時刻
* [ ]	Bedrock呼び出し開始時刻
* [ ]	Bedrockレスポンス受信時刻
* [ ]	Lambda処理終了時刻
* [ ]	APIレスポンス返却時刻

⸻

10. 障害・タイムアウト設計

* [ ]	API Gatewayのタイムアウト時の処理
* [ ]	Lambdaのタイムアウト時の処理
* [ ]	Bedrockのタイムアウト時の処理
* [ ]	Bedrock Throttling時の処理
* [ ]	Bedrockエラー時にリトライするか
* [ ]	リトライ回数
* [ ]	リトライによる二重処理が問題にならないか
* [ ]	クライアント切断時にLambda処理を継続するか
* [ ]	エラーレスポンス形式
* [ ]	非同期処理にする場合のジョブ管理方法
* [ ]	処理結果の保存期間
* [ ]	失敗ジョブの再実行方法

⸻

最初に確認する優先項目

まず以下を確認してからAWS構成を決定する。

優先度：高

* [ ]	Bedrock処理時間
    * [ ]	平均
    * [ ]	p95
    * [ ]	p99
    * [ ]	最大
    * [ ]	30秒超の有無
* [ ]	最大同時利用者数
* [ ]	1日あたりの呼び出し回数
* [ ]	レスポンス方式
    * [ ]	一括レスポンス
    * [ ]	Streaming
    * [ ]	非同期
* [ ]	API公開範囲
    * [ ]	社内
    * [ ]	特定ユーザー
    * [ ]	一般公開
* [ ]	JWTの発行・検証方式

優先度：中

* [ ]	Lambdaコールドスタート時間
* [ ]	Lambdaウォーム時の処理時間
* [ ]	BedrockのQuota
* [ ]	API Gatewayに必要な認証・Rate Limit機能
* [ ]	WAFの必要性
* [ ]	VPCの必要性
* [ ]	月間コスト見積もり

⸻

構成判断

API Gateway

Bedrock処理が確実に30秒以内
+
高度なAPI管理機能が不要
    ↓
HTTP APIを検討
30秒を超える可能性がある
or
外部公開APIとして管理機能を重視
    ↓
REST APIを検討
長時間のAI生成
+
途中結果をユーザーへ返したい
    ↓
Response Streamingを検討
数分以上の処理
+
接続を維持する必要がない
    ↓
非同期APIを検討

Lambda

まず
On-demand Lambda
    ↓
実測
コールドスタートが問題
    ↓
SnapStart / Provisioned Concurrencyを検討
大量同時実行を制御したい
    ↓
Reserved Concurrencyを検討

⸻

現時点の基準構成

現時点では以下を基準案とする。

.NET Framework 4.8 Desktop App
        ↓
API Gateway
        ↓
Lambda
  └─ FastAPI
      ├─ GET /token
      └─ POST /bedrock
              ↓
         Amazon Bedrock

初期候補：

* API Gateway：REST APIを基準に検討
* Lambda：1 Lambda
* Lambda起動方式：On-demand
* アプリケーション：FastAPI
* Bedrock：同期呼び出しから開始
* 認証：JWT
* ログ：CloudWatch
* IAM：Lambda専用実行ロール

Bedrockの実測結果を確認後、以下を再判断する。

* HTTP API / REST API
* 同期 / Streaming / 非同期
* On-demand / SnapStart / Provisioned Concurrency
* Lambda 1個 / 複数