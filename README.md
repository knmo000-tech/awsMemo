# awsMemo

複数顧客企業のWPFアプリからAmazon Bedrockを利用し、生成JSONを取得する非同期APIの設計・検討記録。

**最新の検討は[docsの入口](docs/README.md)から確認してください。** 更新日：2026-10-25。

| 知りたいこと | 資料 |
| --- | --- |
| 今何が決まり、何を検討しているか | [現在の検討状況](docs/current/検討状況.md) |
| REST案とWeb案の違い・構成図 | [入口方式比較](docs/current/入口方式比較.md) |
| 不透明トークンを使う構成・処理 | [構成設計](docs/current/構成設計.md) |
| 各サービスで決めること | [69項目の決定事項一覧](docs/current/決定事項一覧.md) |
| 判断の理由・変更履歴 | [ADR](docs/adr/README.md) |
| 旧設計・旧図・比較の経緯 | [過去資料の案内](docs/archive/README.md) |

## 現在の状態

- 認証は**不透明トークン前提**で設計する。
- 入口は**REST API案・Web Functions案の比較中**。RESTは暫定推奨で、最終決定前。
- 非同期ジョブ、API／Worker分離、DynamoDB、S3のJSON保存と署名URL配信、WPFポーリングの方針を継続。
- SQS Fair Queues、Outbox、入力S3保存、残量予約・精算は提案・検討中。
- AWS環境の構築・デプロイ・負荷試験・費用実測の完了は確認していない。

## ディレクトリ

- `docs/current/`：現在の設計と検討状況の正本
- `docs/adr/`：設計判断の履歴と現在の適用範囲
- `docs/archive/`：旧設計と履歴資料の案内
- `docs/比較検討/`、`docs/diagrams/`、`docs/reviews/`：過去資料。各READMEで最新資料へ案内
- `docs/learning/`：学習用ノート・試算ツール

リポジトリ直下の日付入りメモ・旧図も履歴。最新設計として使わない。旧資料のURLは案内ページ等で可能な限り維持する。
