# セキュリティ・監査設計（導入検討）

> 設計ドラフト / 2026-10-13。**まだAWSに設定したわけではない**。原則としてAPI Gateway REST API + WAFを推奨するが、API Gateway方式とCMK採用は未決定。金額・保持期間・ルール閾値は実環境で見積もること。

## 1. 守りたいもの

- **認証情報**: 保守キー、短期アクセストークン、署名に使う秘密情報
- **顧客情報**: 顧客ID、顧客名、ジョブの所有関係
- **AI入力/出力**: Bedrockに送るテキスト、生成CSV。外部公開してはいけない可能性がある
- **AWS環境**: IAM権限、Lambdaコード、S3/DynamoDBのデータ、請求・利用量
- **監査証跡**: どの顧客がいつ認証・ジョブ実行・結果取得したか、AWS側で誰が構成を変更したか

## 2. 導入の優先度と方針

| サービス/機能 | 担当範囲 | 今回の導入案 | 注意事項 |
| --- | --- | --- | --- |
| **AWS WAF** | インターネットからのHTTP攻撃・大量アクセス軽減 | **推奨**。REST APIステージに紐づけ | すべての不正を防止するものではない。HTTP APIは直接紐づけ不可 |
| **CloudTrail** | AWS管理・API操作の監査 | **推奨**。マルチリージョンのTrailで保存 | Event historyは管理イベントの過去90日。データイベントは別途設定が必要 |
| **GuardDuty** | AWS環境の不審な挙動検出 | **推奨**。検出結果の通知もセットで設計 | 検知サービスでありWAFの代わりではない |
| **AWS KMS** | 暗号鍵の制御・監査 | **要件次第**。S3/DynamoDBの顧客管理キー（CMK）は監査要件を見て採否判断 | デフォルト暗号化も存在。キー料金・API呼び出し料金・IAM設定の負担が増える |
| **CloudWatch** | HTTP/API・Lambdaの運用ログとアラーム | **推奨**。APIアクセスログ + Lambdaアプリ監査ログ | 個人情報・認証情報・生成内容は記録しない |
| **Secrets Manager** | 秘密情報保管・更新 | **推奨**。トークン署名鍵等に使用 | 平文の環境変数やソースコード埋め込みを避ける |
| **CloudWatch Budgets / Cost Anomaly Detection** | Bedrock・WAF等の請求異常 | **推奨** | 予算超過通知は自動的な遮断ではない |

## 3. WAF設計

**案A（推奨）**: WPF → **API Gateway REST API（Regional）+ WAF** → API Lambda（FastAPI+Mangum）。この案なら、REST APIステージにWeb ACLを関連付けられる。

**案B（代替）**: WPF → CloudFront + WAF → API Gateway HTTP API → API Lambda。CloudFrontを経由しないAPI Gateway標準URLへの直接アクセス対策が必要。追加の検証なしに案Bを安全と見なさない。

ルール導入順序案:

1. AWS Managed Rulesの基礎ルール群（まずCountで誤検知を観測）。
2. `POST /auth` にIP等を集約キーとするレートベースルール（閾値は想定利用から決定）。
3. `POST /jobs` にも料金悪用対策としてスロットリング・顧客単位の利用上限。WAFのIP集約は顧客認証・顧客ごとのクォータの代わりにならない。
4. 海外からの利用が不要なら地理制限を**検討**（VPN等を含む正当な利用への影響を先に確認）。
5. WAFログ/CloudWatchメトリクスで誤検知を確認し、必要なルールだけBlockへ変更。

検知したIPをWAFが遮断しても、漏れた正当な保守キー・トークンの悪用を完全には防げない。アプリ側で**キー検証、短期トークン、利用者認可、試行回数制限**が必要。

AWS公式: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html

## 4. CloudTrail設計（AWS操作の監査）

- アカウントのEvent historyで過去90日間の管理イベントを確認可能。ただし**長期監査保存にはTrail**を構成してログをS3へ出力する。
- Trailは全リージョンの管理イベント（読み取り/書き込み）を収集する方針。
- 監査ログ保存用S3バケットは業務CSVバケットと分離、公開アクセスを禁止し、参照主体を制限。保持期限・改ざん防止要件に応じてバージョニング、Object Lock（採用時は運用影響を検討）、ログファイル整合性検証を設計。
- **S3オブジェクトアクセス（GetObject/PutObjectなど）** はCloudTrailのS3データイベントを対象バケットに限定して追加記録することを検討。**LambdaのInvokeも必要に応じてデータイベント**を選択。記録量と料金に注意。
- CloudTrailはAWS側の呼び出し主体（例: Lambda実行ロール）を追うもの。WPF利用者の顧客単位操作はこれだけでは再現できない。

AWS公式: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html

## 5. WPFユーザー単位の監査ログ（CloudWatch等）

次のように**アプリで明示的に記録する**（例）。

```json
{
  "eventType": "JOB_CREATED",
  "timestamp": "2026-10-13T01:00:00Z",
  "customerId": "customer-001",
  "jobId": "example-job-id",
  "requestId": "example-request-id",
  "result": "ACCEPTED"
}
```

認証成功/失敗、ジョブ受付、開始、完了/失敗、CSVダウンロード用URLの発行、管理者による保守キー変更などを記録する。API GatewayアクセスログとLambda構造化ログを `requestId` / `jobId` で関連付ける。

ログに書かないもの: **保守キー、Bearerトークン、リクエスト本文の生データ、Bedrockへのプロンプト/回答全文、署名付きURL、署名秘密鍵**。保存期間、閲覧権限、必要なら改ざん対策を定義する。失敗レスポンスに内部ARN/スタックトレースを返さない。

CloudTrail（AWS操作）とアプリ監査ログ（顧客操作）を**別目的の証跡として併用**する。

## 6. GuardDuty設計

- 基本保護を有効化し、利用リージョンで継続運用する。
- Lambdaを用いるため**Lambda Protection**、CSVをS3保存するため**S3 Protection**の適用を検討する。保護プランはリージョン・ワークロード・料金に応じて選定。
- GuardDutyの検出結果（Findings）をEventBridgeで捕捉してSNS/運用通知先へ通知する。重要度・対象リソース・通知先・一次対応担当者を定める。
- S3 Protectionはオブジェクトレベル操作の脅威を検出するが、CloudTrail TrailのS3データイベント記録を勝手に代替するわけではない（GuardDutyの分析と、監査目的の証跡長期保存は別）。
- 検知のみでは不正操作を止めない。自動隔離などの対処は誤検知時の業務影響を評価して別途実装。

AWS公式: https://docs.aws.amazon.com/guardduty/latest/ug/s3-protection.html

## 7. KMSと暗号化の方針

- **S3**: 新規アップロードは標準で **SSE-S3** により暗号化済み。顧客管理キーで鍵ポリシー・アクセス制御・監査要件を実現したい場合に **SSE-KMS（CMK）** を採用。
- **DynamoDB**: 保存時暗号化は標準で提供。顧客管理キーに切り替える場合はKMSキーの利用権限とサービス統合を別途検証。
- **Secrets Manager**: 短期トークン署名に使う鍵などを保管し、必要なLambdaにのみ取得権限を付与。
- **通信**: WPF→API Gateway、S3署名付きURLダウンロード、AWS APIの呼び出しはTLS前提。KMSは**通信暗号化の代わりではない**。
- **署名付きURL + SSE-KMS** を採用する場合、オブジェクトをGETする署名主体であるAPI Lambda実行ロールに `s3:GetObject` に加え、適切な `kms:Decrypt` 権限が必要。Workerで保存する場合は通常 `s3:PutObject` と `kms:GenerateDataKey` が必要。KMS key policyとIAMの両面を設計。
- KMSのCMKには固定費・API利用料と運用負担がある。最初から全データでCMKを必須化せず、監査要件と脅威分析で採否を決める。

AWS公式: https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html

## 8. 権限と運用設計

- **実行ロール**は API LambdaとWorker Lambdaで分離。API Lambdaに `bedrock:InvokeModel` 権限を付与しない。
- **管理者/デプロイ担当ロール**は実行ロールとは分離。`iam:PassRole` も必要なロールのみに制限する。
- Rootユーザー保護、MFA、定期的な権限棚卸し、CloudWatchアラーム、請求アラートも設計範囲。
- CloudWatchメトリクス: APIの4xx/5xx、認証失敗率、Workerエラー/タイムアウト、ジョブの`QUEUED`滞留、Bedrock呼び出し失敗、GuardDuty High/Critical findings、WAF Block数。
- 本番運用で必要なインシデント対応手順: キー失効、API入口の制限、Worker同時実行数/Bedrock呼び出し抑止、証跡の保全、復旧確認。

## 9. コストに関する注意

WAF（Web ACL/ルール/リクエスト/ログ）、CloudTrail（追加Trail・データイベント・ログ保管）、GuardDuty（分析データ量/オプション）、KMS（CMK数とリクエスト）、CloudWatch Logs（取り込み・保存）、Secrets Manager（シークレット数/呼び出し）は**課金対象になり得る**。構成案確定後にリージョン別の利用量で見積もる。

## 10. 実装前に確認すべきこと

1. 想定API呼び出し数、利用顧客数、ピーク時の認証頻度。
2. REST API+WAF採用の可否、ネットワーク制限（接続元IP制限やVPN利用の有無）。
3. 監査の保存期間と、S3/CSVへのアクセスを誰の操作として記録するか。
4. KMS CMKを必要とする監査/顧客契約要件の有無。
5. 障害通知の送信先、当番、月額運用予算。
6. 保守キーの形式と保管・認証・ローテーション方式。

関連: [構成設計](architecture.md) / [API仕様](api-spec.md) / [シーケンス](sequence.md)
