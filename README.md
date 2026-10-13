# awsMemo

WPF（.NET Framework 4.8）から AWS の Amazon Bedrock を利用してCSVを生成する非同期APIの設計メモです。

## 現在の設計方針（2026-10-13）

- API Gateway経由で **API Lambda 1つ（Python / FastAPI + Mangum）** を利用する。
- 公開エンドポイント: `POST /auth`、`POST /jobs`、`GET /jobs/{jobId}`。
- **Worker Lambda 1つ**がBedrockを非同期実行し、結果CSVをS3に保存する。
- DynamoDBで認証/ジョブを管理。Lambda実行ロールはAPI用とWorker用で分離する。
- WAF・CloudTrail・GuardDuty・KMS・CloudWatch・Secrets Managerの導入範囲を検討している。
- **WAF直接連携のためAPI Gateway REST APIへの変更を推奨**（まだ選定中）。
- ドキュメントは設計ドラフトです。AWS環境への構築・設定はまだ行っていません。

## 設計書

| ファイル | 内容 |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | 全体構成図、Lambda責務、FastAPI、IAMと設計判断 |
| [docs/api-spec.md](docs/api-spec.md) | APIエンドポイント、Request/Response、エラー |
| [docs/sequence.md](docs/sequence.md) | 認証〜非同期Bedrock実行〜CSV取得のフロー |
| [docs/security.md](docs/security.md) | WAF、CloudTrail、GuardDuty、KMS、監査・通知、導入案と未決事項 |

**注意:** 保守キー、署名秘密鍵、トークン、AWSアクセスキー、顧客の実データはGitHubにコミットしないこと。
