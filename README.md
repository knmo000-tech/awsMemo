# awsMemo

複数の顧客企業がWPFアプリからAmazon Bedrockを利用し、生成したJSONを取得する非同期API。

## 2026-10-25：現在の設計前提と入口比較

- **認証は不透明トークンを前提に設計**。以下の旧構成表・履歴図のJWT記述は過去の設計。
- [不透明トークン前提の構成設計・サービス別決定事項](docs/AWS構成設計_不透明トークン前提_2026-10-25.md)：認証・失効、Outbox、残量予約・精算、61項目の決定事項。
- [REST API案とWeb Functions案の構成比較](docs/比較検討/2026-10-25_REST-APIとWeb-Functionsの構成比較.md)：両案の全体構成図、保護設定、比較表、採否の検証条件。
- 入口方式は最終決定前。SQS・Outboxも提案段階で、既存資料の採用ステータスを自動で変更しない。

## 従来の構成（履歴）

| 領域 | 構成 |
| --- | --- |
| クライアント | WPF / .NET Framework 4.8 |
| API | AWS WAF + API Gateway REST API + API Lambda（FastAPI / Mangum） |
| 実行 | Worker Lambda → Amazon Bedrock（非同期）。SQS Fair Queues追加を推奨・検討中 |
| データ | DynamoDB（顧客・ジョブ・使用量）、S3（生成JSON） |
| 認証 | 既存保守キーをDynamoDBで照合 → JWT発行 |
| 取得 | ジョブ状態をポーリング → 署名付きURLでS3からJSON取得 |

## 2026-10-19の更新

- **API入口の第一候補はRegional REST API + WAF直接連携 + 通常Lambda**。HTTP API + CloudFront + WAF、Lambda Web Functionsもゼロベースで比較。
- **非同期・DynamoDB・S3・ポーリングは維持**。100社の並列利用に備え、SQS Standard Fair Queuesを導入推奨（**正式採用・具体設定は未確定**）。
- 月1万・10万・20万ジョブのBtoB稼働日換算、API受付コスト・RPS・Bedrock同時実行の[比較試算](docs/比較検討/2026-10-19_非同期Bedrock基盤とAPI方式の比較.md)を追加。
- **rev4のdraw.io/SVGはSQS追加前の履歴図**。SQS採用後の確定構成図ではない。

## 構成図

- [業務処理・データフロー](docs/diagrams/AWS構成図_rev4_業務フロー.svg)
- [セキュリティ・監査](docs/diagrams/AWS構成図_rev4_セキュリティ監査.svg)
- [draw.io編集ファイル（2ページ）](docs/diagrams/AWS構成図_rev4.drawio)

## 設計資料

| 資料 | 内容 |
| --- | --- |
| [構成設計](docs/構成設計.md) | AWS構成、Lambda、IAM |
| [API仕様](docs/API仕様.md) | エンドポイント、リクエスト・レスポンス、エラー |
| [処理シーケンス](docs/処理シーケンス.md) | 認証からJSON取得まで |
| [セキュリティ・監査](docs/セキュリティ・監査設計.md) | WAF、ログ、検知、秘密情報、暗号化 |
| [請求データ設計メモ](docs/請求データ設計メモ.md) | 使用量記録・権限分離・未決定事項 |
| [設計レビュー資料](docs/reviews/AWS設計レビュー_v0.2.md) | レビュー論点と質問 |
| [ADR](docs/adr/README.md) | 採用・不採用の根拠と判断履歴 |
| [REST APIとWeb Functionsの採用比較（2026-10-20）](docs/比較検討/2026-10-20_REST-APIとWeb-Functions採用比較.md) | 構成図、ユースケース、メリデメ、セキュリティ、料金3ケース、PoCと採否条件 |
| [AWS料金見積もり試算（DynamoDB・S3・WAF・API Gateway）](docs/比較検討/2026-10-20_AWS料金見積もり試算.md) | 100社・月10万ジョブ・10秒ポーリングの入力値と計算式 |
| [2026-10-19 API方式とSQS・概算比較](docs/比較検討/2026-10-19_非同期Bedrock基盤とAPI方式の比較.md) | Web Functions、SQS公平性、月1万・10万・20万件の試算 |

## 操作できる料金シミュレーター

- [REST API vs Web Functions・料金シミュレーター（HTML）](docs/learning/AWS料金シミュレーター.html)：スライダー・3ケース切替・内訳・損益分岐点。ブラウザで直接開くかGitHub Pagesで配信して利用（GitHubのコード表示画面では操作不可）。

## 個人学習用

[構成の理解ノート（Markdown）](docs/learning/AWS構成の理解ノート.md) / [ブラウザで読む（HTML）](docs/learning/AWS構成の理解ノート.html)

## 未確定事項

- 使用量データの物理テーブル設計と請求計算の詳細
- Bedrockでトークン消費後、成果物の生成・保存・取得に失敗した場合の請求可否
- ジョブの再試行・二重計上防止、保持期間、監査・通知の具体設定
