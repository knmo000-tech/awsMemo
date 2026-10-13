# AWS構成図 — リビジョン管理

| 版 | 編集用 | 画像プレビュー | 内容 |
| --- | --- | --- | --- |
| **rev1** | [draw.io](aws-architecture-rev1.drawio) | [SVG](aws-architecture-rev1.svg) | 変更前の構成を凍結保存。DynamoDBは1つのサービス枠 |
| **rev2** | [draw.io](aws-architecture-rev2.drawio) | [SVG](aws-architecture-rev2.svg) | **今回の推奨採用案**。CSV保存・監査ログ連携を明示 |
| 旧互換パス | [draw.io](aws-architecture.drawio) | [SVG](aws-architecture.svg) | rev1相当の旧リンク（既存の参照用） |

![rev2 AWS構成図](aws-architecture-rev2.svg)

## rev2で採用する方向のサービス

- **AWS WAF + API Gateway REST API**: インターネット公開APIの保護とアクセス制限。HTTP APIへのWAF直接接続はできないためREST APIを推奨。
- **CloudWatch**: API Gatewayアクセスログ、API Lambda/Worker Lambdaの実行・アプリ監査ログ、メトリクス・アラーム。
- **CloudTrail**: AWS管理イベントと請求用DynamoDB操作の必要なデータイベントを記録し、監査用S3に保存。
- **GuardDuty**: 不審な活動の検知。検出結果の通知はEventBridge/SNS等で**別途構築が必要**。S3 Protection/Lambda Protectionなど有料オプションは利用量・要件次第で個別判断。
- **Secrets Manager**: 認証トークン署名に使う秘密情報の保管・管理。利用する鍵方式によって要再評価。
- **S3**: Worker Lambdaで生成したCSVを非公開保管し、API Lambdaが顧客の所有者照合後に署名付きURLを発行。請求監査証跡は別の保存先として管理。

これらは**設計上の推奨採用構成**であり、AWSにデプロイ済み・IAM設定済みではありません。

## 引き続き検討中・今回は採用しないもの

- **DynamoDB UsageEventsの物理別テーブル化**: 課金根拠を分離する案は維持するが、物理設計は未確定。
- **S3 Object Lock**: 請求明細/監査ログの改ざん耐性と保持期間の要件が決まるまで検討中。
- **専用AWS KMSカスタマー管理キー**: **現時点で不採用**。標準的な保存時暗号化（DynamoDB、S3 SSE-S3）は継続。
- **CloudFront＋HTTP API方式**: REST API＋WAFの代替案として記録、rev2には採用しない。

## 接続線について

- 実線: アプリの業務通信（WPF→API→Worker→Bedrock / Worker→CSVのS3保存など）
- 破線: ログ収集・監査・秘密情報の読み出し・請求テーブル検討などの補助的な関係
- GuardDutyは監視情報を分析するサービスであり、すべての業務リクエストがGuardDutyを経由する意味ではありません。
- CloudTrailはAWS操作の証跡、CloudWatch/アプリログはAPI顧客操作と障害追跡に利用します。

## AWSアイコン素材

AWS公式アイコン: https://aws.amazon.com/architecture/icons/  
図の生成時に参照した公開カタログ: https://github.com/phergoualch/aws-icons

判断の経緯は [ADR一覧](../adr/README.md) を参照。図のrev2は設計比較用の版として扱い、正式な採用判断はADRで記録する。
