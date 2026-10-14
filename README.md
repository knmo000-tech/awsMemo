# awsMemo

複数の顧客企業がWPFアプリからAmazon Bedrockを利用し、生成したJSONを取得する非同期API。

## 構成

| 領域 | 構成 |
| --- | --- |
| クライアント | WPF / .NET Framework 4.8 |
| API | AWS WAF + API Gateway REST API + API Lambda（FastAPI / Mangum） |
| 実行 | Worker Lambda → Amazon Bedrock（非同期） |
| データ | DynamoDB（顧客・ジョブ・使用量）、S3（生成JSON） |
| 認証 | 既存保守キーをDynamoDBで照合 → JWT発行 |
| 取得 | ジョブ状態をポーリング → 署名付きURLでS3からJSON取得 |

## 構成図

- [業務処理・データフロー](docs/diagrams/aws-architecture-rev4-business.svg)
- [セキュリティ・監査](docs/diagrams/aws-architecture-rev4-security.svg)
- [draw.io編集ファイル（2ページ）](docs/diagrams/aws-architecture-rev4.drawio)

## 設計資料

| 資料 | 内容 |
| --- | --- |
| [構成設計](docs/architecture.md) | AWS構成、Lambda、IAM |
| [API仕様](docs/api-spec.md) | エンドポイント、リクエスト・レスポンス、エラー |
| [処理シーケンス](docs/sequence.md) | 認証からJSON取得まで |
| [セキュリティ・監査](docs/security.md) | WAF、ログ、検知、秘密情報、暗号化 |
| [請求データ設計メモ](docs/billing-data-design-notes.md) | 使用量記録・権限分離・未決定事項 |
| [設計レビュー資料](docs/reviews/aws-design-review-v0.2.md) | レビュー論点と質問 |
| [ADR](docs/adr/README.md) | 採用・不採用の根拠と判断履歴 |

## 個人学習用

[構成の理解ノート（Markdown）](docs/learning/aws-architecture-guide.md) / [ブラウザで読む（HTML）](docs/learning/aws-architecture-guide.html)

## 未確定事項

- 使用量データの物理テーブル設計と請求計算の詳細
- Bedrockでトークン消費後、成果物の生成・保存・取得に失敗した場合の請求可否
- ジョブの再試行・二重計上防止、保持期間、監査・通知の具体設定
