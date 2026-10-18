# Architecture Decision Records (ADR) — 設計判断の記録

> 最終更新: 2026-10-19 / 対象: 複数の顧客企業がインターネット経由で利用する WPF → AWS → Bedrock の非同期JSON生成サービス。

本ディレクトリは、**何を採用／不採用にしたか、判断の理由と経緯、再検討条件**を記録する。アプリの実装状況やAWSへのデプロイ完了を意味しない。詳細な構成は [構成設計](../構成設計.md)、[セキュリティ設計](../セキュリティ・監査設計.md)を参照。

## 記録ルール

- **採用（設計確定）**: 方式を選んだ段階。AWSへの実装済みとは区別する。
- **不採用（現時点）**: 比較したうえで今は選ばない。代替案・見直し条件を必ず残す。
- **検討中**: 提案はあるが最終決定していない。推奨を確定事項として扱わない。
- **計画**: 必要性・原則は合意しているが、製品選定や運用設計が残る。
- 各ADRは日付・背景・決定・採用理由・不採用案・トレードオフ・見直し条件を記載。決定変更時は古い理由を消さず、新たなADRを作り `Superseded by` でリンクする。
- AWS構築済／未実装などの実施状況は別途管理する。

## 判断一覧（2026-10-19）

| ID | 対象（サービス・構成） | 現在の方針 | 状態 | 主な判断理由 |
| --- | --- | --- | --- | --- |
| [ADR-0001](0001_FastAPI採用.md) | FastAPI / Mangum / Python Lambda | API LambdaでFastAPI+Mangum採用 | **採用** | 3エンドポイントの管理、型検証、将来の拡張性 |
| [ADR-0002](0002_API処理とWorker分離.md) | Lambda / API Gateway / Bedrock | API Lambda 1 + Worker Lambda 1、非同期 | **採用** | API受付とAI実行の権限・タイムアウト・障害分離 |
| [ADR-0003](0003_生成物保管と請求実績.md) | DynamoDB / S3 / UsageEvents | 顧客・ジョブをDynamoDB、生成物（現在はJSON）をS3に保存。請求トークン実績をサーバー側で記録 | **採用（原則）／明細設計は検討中** | 顧客単位の認可・ジョブ追跡、実消費に基づく請求の再現性 |
| [ADR-0004](0004_専用KMSキー不採用.md) | AWS KMS / DynamoDB / S3 | **専用のKMS顧客管理キーを追加採用しない**。標準暗号化を利用 | **不採用（現時点）** | KMSでは正規権限での請求データ改ざんを防げず、まず整合性・証跡・復旧を優先 |
| [ADR-0005](0005_REST-APIとWAF採用.md) | API Gateway HTTP/REST / WAF / CloudFront | REST API + WAFを採用、追加APIキー不要 | **採用** | 外部公開APIを守りつつ運用構成を簡素化 |
| [ADR-0006](0006_監査とセキュリティ.md) | CloudTrail / GuardDuty / CloudWatch / Secrets Manager / AWS Budgets | Secrets ManagerはJWT署名鍵管理として採用。他サービスは詳細設計中 | **一部採用・他は検討中** | AWS操作監査・脅威検出・顧客操作監査・秘密情報管理を分離 |
| [ADR-0007](0007_JSON出力採用.md) | 生成物の形式 | JSONをS3に保存、ポーリングと非同期構成は維持 | **採用** | 成果物の要件がJSONに変更され、既存の非同期処理は維持するため |

| [ADR-0008](0008_Web-Functions比較.md) | Lambda Web Functions | REST API + WAF + 通常Lambdaを第一候補 | **Web Functions不採用** | 既存言語の移行負担を無視してもWAF直接連携と運用の単純さを重視 |
| [ADR-0009](0009_SQS公平キュー導入検討.md) | SQS Fair Queues | 追加を推奨、詳細未決定 | **検討中** | Bedrock流量制御と企業間の待ち時間の偏りを軽減 |

## 決定の経緯

| 日付 | 経緯 |
| --- | --- |
| 2026-10-07 | 当初はFastAPIなしのLambdaハンドラー案を検討。その後FastAPI採用へ変更。API処理とBedrock処理を2つのLambdaに分離する方針を決定 |
| 2026-10-13 | 公開APIの保護としてWAF、CloudTrail、GuardDuty、KMSを検討開始。API Gateway REST API + WAFを推奨案として保留 |
| 2026-10-13 | 利用主体が**複数顧客企業**と判明。Bedrockの**トークン使用量を独自計算の請求根拠としてDBに保持**する要件を追加 |
| 2026-10-13 | 請求データの改ざん対策はKMSではなくIAM制限・追記型実績・監査・復旧が中心と整理。**KMS顧客管理キーを現時点で採用しないことを決定** |
| 2026-10-13 | REST API + WAFの採用を確定。API Gatewayの追加APIキーは使わず、既存保守キー照合→JWT発行の認証方式を維持。自前JWTの署名鍵管理にSecrets Managerを採用 |
| 2026-10-15 | 成果物をCSVからJSONへ変更。Lambda2関数、S3保存、ポーリングなど構成は維持（[ADR-0007](0007_JSON出力採用.md)） |

| 2026-10-15 | Lambda Web Functionsを比較検討し、現行のAPI Gateway REST API + WAF / Python FastAPI構成を維持する方針を確認（[ADR-0008](0008_Web-Functions比較.md)） |

## 更新時のチェックリスト

- 既存ADRのstatusに矛盾がないか
- `構成設計.md`、`セキュリティ・監査設計.md`、`API仕様.md` と齟齬がないか
- 代替案を採用しなかった理由と、再検討する条件が明記されているか
- 採用方針とAWS実装済みの事実を混同していないか

## 2026-10-19の更新

- REST API + WAF + 通常Lambdaを、Web Functions・HTTP APIも含むゼロベース比較で第一候補として再確認（[ADR-0008](0008_Web-Functions比較.md)）。
- SQS Fair Queuesは導入推奨だが正式決定ではない（[ADR-0009](0009_SQS公平キュー導入検討.md)）。
- 100社、月1万・10万・20万ジョブの机上試算は[比較資料](../比較検討/2026-10-19_非同期Bedrock基盤とAPI方式の比較.md)参照。
- ドキュメント名を原則日本語化（GitHubが既定表示するREADME.mdのみ慣例上維持）。
