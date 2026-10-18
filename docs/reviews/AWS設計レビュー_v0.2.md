# AWS Bedrock連携システム — 設計レビュー

## システム構成

[業務処理図](../diagrams/AWS構成図_rev4_業務フロー.svg) / [セキュリティ・監査図](../diagrams/AWS構成図_rev4_セキュリティ監査.svg)

WPF → WAF → API Gateway REST API → API Lambda（FastAPI + Mangum）→ Worker Lambda → Bedrock。生成JSONはWorkerがS3に保存し、WPFがジョブ状態をポーリングして署名付きURLから取得する。

## 構成・代替案の要点

| 論点 | 採用方式 | 代替案・確認事項 |
| --- | --- | --- |
| API入口 | REST API + WAF | HTTP API + CloudFront + WAFは構成・迂回対策が増える |
| 認証 | 既存保守キー＋顧客名をDynamoDB照合 → JWT | API Gatewayの追加APIキーは不要。キー管理・失効方法は要設計 |
| API実装 | API Lambda 1関数にFastAPI + Mangum | ルート別Lambdaは関数・デプロイ管理が増える |
| AI実行 | 独立Worker Lambdaを非同期Invoke | 同期実行は処理時間とAPIタイムアウトの影響を受ける |
| 長時間処理 | Jobsに状態保存しポーリング | SQS/Step Functionsは必要な信頼性・負荷に応じて追加検討 |
| 生成物 | JSONをS3へ保存し短命URLで取得 | API Lambda経由転送は採らない。JSON最大約1MBを想定 |
| DB | DynamoDBでCustomers / Jobs管理 | UsageEventsの物理別テーブル化は未決定 |
| 請求実績 | Bedrock由来の実使用量をサーバー側で記録 | クライアント申告値は請求根拠にしない |
| 秘密情報 | Secrets ManagerでJWT署名鍵を管理 | 鍵アルゴリズム、更新・失効は未決定 |
| 暗号化 | DynamoDB標準暗号化、S3 SSE-S3 | 専用KMS顧客管理キーは採用しない |
| 監視・監査 | CloudWatch、CloudTrail、GuardDuty | 保存期間・通知先・追加保護機能を設計する |

## 重要な制御

- API LambdaとWorker LambdaのIAM実行ロールを分離。Bedrock実行権限はWorkerだけ。
- 顧客ごとの認可とジョブ所有者チェックを実施。S3への直接アクセスは短命な署名付きURLを利用。
- 使用量の追記・冪等性・監査・DynamoDB PITRを組み合わせ、二重請求や記録漏れに備える。
- ログへ保守キー、JWT、プロンプト全文、生成JSON、署名付きURLを出さない。

## レビューで確定したい項目

1. Bedrockでトークンを消費後、JSON生成・保存・取得に失敗した場合の請求可否。
2. 非同期Workerの再実行・二重計上・使用量記録漏れへの対処とSQS等の要否。
3. 保守キー・JWTの有効期限、漏えい・失効・鍵更新方法。
4. 顧客別の利用量上限、課金単価・計算方法、月次請求明細の保全。
5. JSONスキーマ、成果物・監査ログの保存期間、WAF閾値、障害通知先。

## 2026-10-19 追記

上記の比較表とrev4構成図は元のレビュー時点の設計を示す履歴である。現在はREST API + WAFを第一候補と再確認し、SQS Fair Queuesを導入推奨の検討候補とした。非同期、結果S3保管、ジョブDynamoDB管理は維持。100社・月1万/10万/20万ジョブの試算は[比較資料](../比較検討/2026-10-19_非同期Bedrock基盤とAPI方式の比較.md)、[ADR-0009](../adr/0009_SQS公平キュー導入検討.md)参照。

