# AWS構成設計

[業務構成図](diagrams/aws-architecture-rev4-business.svg) / [監査構成図](diagrams/aws-architecture-rev4-security.svg) / [draw.io](diagrams/aws-architecture-rev4.drawio)

## システム構成

| コンポーネント | 役割 |
| --- | --- |
| WPF（.NET Framework 4.8） | 保守キーによる認証、ジョブ投入、結果ポーリング、JSON取得 |
| AWS WAF + API Gateway REST API | 公開HTTPS API、WAF検査、Lambdaへの転送。API Gateway APIキーは不要 |
| API Lambda（FastAPI + Mangum） | `POST /auth`、`POST /jobs`、`GET /jobs/{jobId}` |
| Worker Lambda | 非同期実行、Bedrock呼び出し、利用量記録、JSONのS3保存 |
| DynamoDB | `Customers`（認証）、`Jobs`（状態）。`UsageEvents`は論理データ領域の候補 |
| Amazon S3 | 生成JSONを非公開で保存（`application/json`）。短命な署名付きURLで配信 |
| Secrets Manager | JWT署名用秘密鍵をAPI Lambdaへ提供 |

## 処理

1. WPFが`POST /auth`で保守キー・顧客名を送信。API LambdaがDynamoDBで照合し、JWTを発行。
2. WPFがJWT付きで`POST /jobs`を呼び出す。API Lambdaがジョブを`QUEUED`で登録し、Worker Lambdaを非同期起動して`202 + jobId`を返す。
3. Workerが`RUNNING`へ更新し、Bedrockを呼び出す。生成JSON（最大約1MBを想定）をS3に保存し、利用量・ジョブ状態を記録する。
4. WPFは`GET /jobs/{jobId}`をポーリング。API LambdaがJWTとジョブ所有者を検証して状態を返す。
5. 成功時、API Lambdaが短命なS3署名付きURLを返す。WPFが**Lambdaを経由せずS3から直接**JSONを取得する。

ジョブ状態：`QUEUED → RUNNING → SUCCEEDED / FAILED`。結果取得・請求実績記録の障害時も調査できる設計とする。

## IAM実行権限

| 実行ロール | 許可アクション | リソース |
| --- | --- | --- |
| API Lambda | `dynamodb:GetItem` / 必要時`Query`、`dynamodb:PutItem` | Customers参照、Jobs登録・参照 |
| API Lambda | `lambda:InvokeFunction` | Worker Lambdaのみ |
| API Lambda | `s3:GetObject` | 成果物の署名付きURLの発行 |
| API Lambda | `secretsmanager:GetSecretValue` | JWT署名鍵 |
| Worker Lambda | `bedrock:InvokeModel` | 利用を許可したモデル・推論プロファイル |
| Worker Lambda | `dynamodb:UpdateItem` | Jobs状態更新 |
| Worker Lambda | `s3:PutObject` | 生成JSONの保存先 |
| Worker Lambda（使用量記録案） | `dynamodb:PutItem` | 使用量イベント新規登録 |
| 両Lambda | CloudWatch Logsへの書き込み | 各関数のロググループ |

IAMは実ARN・必要な操作に限定。API LambdaにはBedrock呼び出し権限を付与しない。デプロイ担当ロールはLambda実行ロールと分離する。

## 実装上の要点

- API GatewayはREST APIのLambdaプロキシ統合。FastAPIのASGIイベント変換にMangumを使用。
- FastAPI/Mangum等はLambdaのデプロイパッケージ（ZIPまたはコンテナ）に同梱。
- JWTの署名・期限・顧客ID・所有者を検証。保守キーの平文保存・機密値のログ出力は禁止。
- 使用量はBedrock側で得た値を記録し、重複起動・再試行時の二重計上を防止する。
- S3は非公開・標準暗号化（SSE-S3）。DynamoDBも標準暗号化を利用。専用KMS顧客管理キーは使用しない。

## 詳細設計で決める項目

- Bedrockモデル、JSONスキーマ、サイズ・処理時間・ジョブ保持期間
- 冪等性、非同期起動失敗・滞留ジョブの扱い、利用量記録漏れ時の補正
- `UsageEvents`の物理構造、顧客別上限、請求ルール
