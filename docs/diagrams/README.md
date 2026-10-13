# AWS構成図（draw.io + SVG）

- [編集用 aws-architecture.drawio](aws-architecture.drawio) — diagrams.netで開き、サービスの位置・説明・接続線を編集できる
- [表示用 aws-architecture.svg](aws-architecture.svg) — GitHubとスマートフォンのブラウザで表示するプレビュー
- 親ページ: [awsMemo README](../../README.md)

## 対応するシステム

- 顧客企業のWPFアプリ → AWS WAF（導入提案） → API Gateway REST API（推奨案） → API Lambda（FastAPI + Mangum）
- API LambdaからWorker Lambdaを非同期呼び出しし、WorkerがAmazon Bedrockを呼ぶ
- DynamoDB Customers / Jobs、生成CSVのS3保存
- **UsageEventsの物理的な別テーブル化は未決定**。請求実績の分離・権限制御・監査の検討内容は [請求データ設計メモ](../billing-data-design-notes.md) を参照
- CloudTrail、GuardDuty、CloudWatch、Secrets Manager、請求監査証跡S3は導入・運用設計の検討対象
- 専用AWS KMSカスタマー管理キーは現時点で不採用。DynamoDBの標準暗号化・S3 SSE-S3は維持

## 図の凡例

| 表示 | 意味 |
| --- | --- |
| 青 | 採用方針の業務構成 |
| 黄 | 推奨案であり、まだ最終採用を確定していない |
| 紫・破線 | データ構造の検討候補 |
| グレー | セキュリティ・監査サービス（採用範囲・設定は検討段階） |

**重要:** 構成図は「採用・提案している設計」を可視化したもので、AWS環境へのデプロイ済みを示すものではありません。変更の理由は [ADR一覧](../adr/README.md) に記録します。

## AWSアイコン素材

AWS Architecture Iconsに由来するサービスアイコンを図内に組み込んでいます。

- AWS公式のArchitecture Icons配布・利用ガイド: https://aws.amazon.com/architecture/icons/
- 今回参照したサービスSVGの公開カタログ: https://github.com/phergoualch/aws-icons
- `.drawio`にはSVGをデータとして埋め込み、`.svg`プレビューにも同じベクター形状を組み込みました。

サービス名・AWSの商標とアイコンはAmazon Web Servicesのものです。図の作成・更新時にはAWS公式アイコンの利用条件も確認してください。

## 更新時の注意

1. 編集用の`.drawio`を正本として変更する。
2. プレビューの`.svg`を再出力・更新し、READMEで旧図が表示されないか確認する。
3. ADRや設計書で確定/検討中の状態が変わっていたら、凡例・ラベル・説明も揃える。
4. 改行や長いサービス名による文字の重なり、矢印の交差を最終確認する。
