# セキュリティ・監査設計（導入検討）

> 設計ドラフト / 2026-10-13（成果物形式を2026-10-15にJSONへ変更）。**まだAWSに設定したわけではない**。原則としてAPI Gateway REST API + WAFを推奨する（REST API＋WAFは採用決定）。**専用KMSカスタマー管理キーは現時点で不採用と決定済み**。金額・保持期間・ルール閾値は実環境で見積もること。

## 1. 守りたいもの

- **認証情報**: 保守キー、短期アクセストークン、署名に使う秘密情報
- **顧客情報**: 顧客ID、顧客名、ジョブの所有関係
- **AI入力/出力**: Bedrockに送るテキスト、生成JSON。外部公開してはいけない可能性がある
- **AWS環境**: IAM権限、Lambdaコード、S3/DynamoDBのデータ、請求・利用量
- **監査証跡**: どの顧客がいつ認証・ジョブ実行・結果取得したか、AWS側で誰が構成を変更したか
- **最重要：請求実績**: 顧客別のBedrock実トークン使用量と、その根拠から算出する料金の正確性・追跡可能性・復旧可能性

## 2. 導入の優先度と方針

| サービス/機能 | 担当範囲 | 今回の導入案 | 注意事項 |
| --- | --- | --- | --- |
| **AWS WAF** | インターネットからのHTTP攻撃・大量アクセス軽減 | **採用決定**。REST APIステージに紐づけ | すべての不正を防止するものではない。HTTP APIは直接紐づけ不可 |
| **CloudTrail** | AWS管理・API操作の監査 | **推奨**。マルチリージョンのTrailで保存 | Event historyは管理イベントの過去90日。データイベントは別途設定が必要 |
| **GuardDuty** | AWS環境の不審な挙動検出 | **推奨**。検出結果の通知もセットで設計 | 検知サービスでありWAFの代わりではない |
| **AWS KMS（専用カスタマー管理キー）** | 独自の鍵制御・利用監査 | **不採用（現時点）**。DynamoDB既定の保存時暗号化・S3 SSE-S3を利用 | 請求トークン使用量の改ざん防止はKMSだけでは実現できず、整合性・監査・復旧を優先。顧客要件が変われば再検討 |
| **CloudWatch** | HTTP/API・Lambdaの運用ログとアラーム | **推奨**。APIアクセスログ + Lambdaアプリ監査ログ | 個人情報・認証情報・生成内容は記録しない |
| **Secrets Manager** | 秘密情報保管・更新 | **採用決定**。自前JWTの署名鍵を保管 | 平文の環境変数やソースコード埋め込みを避ける |
| **AWS Budgets / Cost Anomaly Detection** | Bedrock・WAF等の請求異常 | **推奨** | 予算超過通知は自動的な遮断ではない |

## 3. WAF設計

**案A（採用）**: WPF → **API Gateway REST API（Regional）+ WAF** → API Lambda（FastAPI+Mangum）。この案なら、REST APIステージにWeb ACLを関連付けられる。

**案B（不採用の代替案）**: WPF → CloudFront + WAF → API Gateway HTTP API → API Lambda。CloudFrontを経由しないAPI Gateway標準URLへの直接アクセス対策が必要。追加の検証なしに案Bを安全と見なさない。

ルール導入順序案:

1. AWS Managed Rulesの基礎ルール群（まずCountで誤検知を観測）。
2. `POST /auth` にIP等を集約キーとするレートベースルール（閾値は想定利用から決定）。
3. `POST /jobs` にも料金悪用対策としてスロットリング・顧客単位の利用上限。WAFのIP集約は顧客認証・顧客ごとのクォータの代わりにならない。
4. 海外からの利用が不要なら地理制限を**検討**（VPN等を含む正当な利用への影響を先に確認）。
5. WAFログ/CloudWatchメトリクスで誤検知を確認し、必要なルールだけBlockへ変更。

検知したIPをWAFが遮断しても、漏れた正当な保守キー・トークンの悪用を完全には防げない。アプリ側で**キー検証、短期トークン、利用者認可、試行回数制限**が必要。

AWS公式: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html

**認証・APIキー方針（決定済み）:** API Gateway REST APIの`apiKeyRequired`を`false`にする。WPFには既存保守キーのみを使用し、`POST /auth`のFastAPIでDynamoDB照合後にJWTを発行。`/jobs`ではJWTを検証する。API Gatewayの追加APIキーは配布しない。JWT署名秘密鍵はSecrets Managerで管理する。署名方式・鍵更新時の旧トークン検証・失効は別途設計する。

## 4. CloudTrail設計（AWS操作の監査）

- アカウントのEvent historyで過去90日間の管理イベントを確認可能。ただし**長期監査保存にはTrail**を構成してログをS3へ出力する。
- Trailは全リージョンの管理イベント（読み取り/書き込み）を収集する方針。
- 監査ログ保存用S3バケットは業務JSONバケットと分離、公開アクセスを禁止し、参照主体を制限。保持期限・改ざん防止要件に応じてバージョニング、Object Lock（採用時は運用影響を検討）、ログファイル整合性検証を設計。
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

認証成功/失敗、ジョブ受付、開始、完了/失敗、JSONダウンロード用URLの発行、管理者による保守キー変更などを記録する。API GatewayアクセスログとLambda構造化ログを `requestId` / `jobId` で関連付ける。

ログに書かないもの: **保守キー、Bearerトークン、リクエスト本文の生データ、Bedrockへのプロンプト/回答全文、署名付きURL、署名秘密鍵**。保存期間、閲覧権限、必要なら改ざん対策を定義する。失敗レスポンスに内部ARN/スタックトレースを返さない。

CloudTrail（AWS操作）とアプリ監査ログ（顧客操作）を**別目的の証跡として併用**する。

## 6. GuardDuty設計

- 基本保護を有効化し、利用リージョンで継続運用する。
- Lambdaを用いるため**Lambda Protection**、JSONをS3保存するため**S3 Protection**の適用を検討する。保護プランはリージョン・ワークロード・料金に応じて選定。
- GuardDutyの検出結果（Findings）をEventBridgeで捕捉してSNS/運用通知先へ通知する。重要度・対象リソース・通知先・一次対応担当者を定める。
- S3 Protectionはオブジェクトレベル操作の脅威を検出するが、CloudTrail TrailのS3データイベント記録を勝手に代替するわけではない（GuardDutyの分析と、監査目的の証跡長期保存は別）。
- 検知のみでは不正操作を止めない。自動隔離などの対処は誤検知時の業務影響を評価して別途実装。

AWS公式: https://docs.aws.amazon.com/guardduty/latest/ug/s3-protection.html

## 7. KMS不採用と請求データの保護方針（決定済み）

### 結論

**専用のAWS KMSカスタマー管理キーは現時点で採用しない。** これは暗号化を廃止する意味ではない。DynamoDBの標準的な保存時暗号化、S3のSSE-S3およびTLSを利用する。

今回の最重要データは、複数顧客企業に対する独自請求の根拠になるBedrockトークン使用量である。KMSによる保存時暗号化は、適切なDynamoDB書き込み権限を持つ主体が請求データを変更すること自体は防げないため、**完全性・重複排除・証跡・復旧**を直接保護する対策を先行する。

### 採用しない理由

1. キーを自前管理しても、正当に許可されたDB更新による誤請求や改ざんの防止には直結しない。
2. カスタマー管理キーの鍵ポリシー、ローテーション、無効化、費用、運用負荷が増える。
3. 現時点では、顧客との契約や監査要件から独自の暗号鍵管理を要求されていない。

### 請求データのために優先する制御

| 脅威 | 対策 | 現状 |
| --- | --- | --- |
| 請求用トークン実績の上書き | UsageEventsの追記型イベント、既存値の上書きを禁止するDynamoDB条件付き書き込み | 物理設計を検討中 |
| 無権限の操作 | API/WorkerのIAM最小権限、課金データの更新権限をさらに限定 | 設計方針 |
| リトライによる二重計上 | 呼び出し一意ID・冪等性・請求集計の重複排除 | 詳細検討中 |
| 操作の証拠不足 | CloudTrailのDynamoDBデータイベント、アプリ監査ログ | 導入計画 |
| 誤削除・破損 | DynamoDB PITR、復元手順の検証 | 導入計画 |
| 請求紛争 | 計算単価バージョン付き明細、確定版の保全とS3 Object Lockの評価 | 検討中 |

**PITRは復旧用であり、独立した長期の改ざん防止ではない。** CloudTrailイベントのみでDynamoDBアイテムの変更前後の内容が自動的に保存されるわけではない。請求明細の確定と保存方法は別途設計する。

### 代替案と再評価

- **専用KMSカスタマー管理キー**: 見送り。顧客契約上の暗号鍵管理や監査要件が発生したら再評価する。
- **暗号化なし**: 不採用。AWSサービス標準の保存時暗号化は使用する。
- Secrets Managerの保護やAWSサービス内部の暗号化でKMS関連の機構が使われる場合がある。**今回の不採用判断はAWS KMSが環境内で一切使われないことを意味しない**。

判断の背景・代替案・見直し条件は [ADR-0004](adr/0004-no-customer-kms.md)、請求データの設計背景は [ADR-0003](adr/0003-storage-billing.md) を参照。

## 8. Bedrock固有の監査・情報保護

- Bedrockへの呼び出しはWorker Lambdaが行う。CloudTrailのAWS操作証跡と、アプリ監査ログの `jobId` / `customerId` を関連づける。
- Bedrockの**モデル呼び出しログ（Model invocation logging）**の導入は、顧客データの取り扱い方針と保存先のアクセス管理・保存期限を確認してから判断する。設定によっては**プロンプトやモデル応答そのものがログに含まれる**ため、無条件では有効にしない。
- 顧客ごとの月間上限、同時実行数、Workerの予約済み同時実行、Bedrockクォータ、異常請求検知を組み合わせる。WAFだけでAI利用料金の悪用を防げるわけではない。

AWS公式: https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html

## 9. 権限と運用設計

- **実行ロール**は API LambdaとWorker Lambdaで分離。API Lambdaに `bedrock:InvokeModel` 権限を付与しない。
- **管理者/デプロイ担当ロール**は実行ロールとは分離。`iam:PassRole` も必要なロールのみに制限する。
- Rootユーザー保護、MFA、定期的な権限棚卸し、CloudWatchアラーム、請求アラートも設計範囲。
- CloudWatchメトリクス: APIの4xx/5xx、認証失敗率、Workerエラー/タイムアウト、ジョブの`QUEUED`滞留、Bedrock呼び出し失敗、GuardDuty High/Critical findings、WAF Block数。
- 本番運用で必要なインシデント対応手順: キー失効、API入口の制限、Worker同時実行数/Bedrock呼び出し抑止、証跡の保全、復旧確認。

## 10. コストに関する注意

WAF（Web ACL/ルール/リクエスト/ログ）、CloudTrail（追加Trail・データイベント・ログ保管）、GuardDuty（分析データ量/オプション）、CloudWatch Logs（取り込み・保存）、Secrets Manager（シークレット数/呼び出し）は**課金対象になり得る**。構成案確定後にリージョン別の利用量で見積もる。

## 11. 実装前に確認すべきこと

1. 想定API呼び出し数、利用顧客数、ピーク時の認証頻度。
2. **REST API＋WAFは採用確定**。ネットワーク制限（接続元IP制限やVPN利用の有無）。
3. 監査の保存期間と、S3/JSONへのアクセスを誰の操作として記録するか。
4. **KMSのカスタマー管理キーは現時点で不採用**。将来の顧客契約・監査要求が変更された場合のみ再評価。
5. 障害通知の送信先、当番、月額運用予算。
6. 保守キーの形式と保管・認証・ローテーション方式。

関連: [構成設計](architecture.md) / [API仕様](api-spec.md) / [シーケンス](sequence.md) / [設計判断記録（ADR）](adr/README.md)
