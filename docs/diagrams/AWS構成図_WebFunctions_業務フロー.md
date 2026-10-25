# Web Functions案：業務処理・データの流れ

作成日：2026-10-26。**比較・検証用の設計図であり、採用確定・AWSへの構築完了を意味しない。**

[SVGを開く](AWS構成図_WebFunctions_業務フロー.svg) / [シーケンス図](AWSシーケンス図_WebFunctions.md) / [入口方式比較](../current/入口方式比較.md) / [構成設計](../current/構成設計.md) / [図の一覧](README.md)

![Web Functions案の業務フロー](AWS構成図_WebFunctions_業務フロー.svg)

## 図の範囲

`AWS構成図_rev4_業務フロー.svg`と同程度の粒度で、公開入口、API処理、データ領域、生成処理、結果取得を示す。rev4のJWT・直接Invokeは踏襲せず、現在の`docs/current/`の不透明トークン前提と、両入口で揃えて比較する非同期処理案に合わせた。

- 青実線：業務通信・データ操作。双方向矢印は要求と応答、または読み書きをまとめたもの。
- 紫破線：応答、関連付け、提案の非同期配送、結果取得など。破線だけで「未決」を表さない。
- 紫の枠：SQS・Outbox・配送処理等の提案。Web案そのものも最終選定前。
- DynamoDB内の名称は論理領域。物理テーブル数・キー設計は未決。
- 監査サービスは下部に利用計画を記載。監査用データ経路の詳細はこの業務フロー図に含めない。

## 認証から取得まで

| 段階 | 通信・処理 | データ・責任 |
| --- | --- | --- |
| 1：認証 | WPF → CloudFront → Webの`POST /auth` | Customersで保守キー・顧客状態を照合。不透明トークンを発行しSessionsへ保存。ハッシュ保存等の詳細は構成設計の提案に従う |
| 2：受付 | `POST /jobs`、Bearer、Idempotency-Key、入力 | セッションと顧客を検証。提案：入力を先にS3保存し、冪等性・残量予約・Jobs・Outboxを原子的に登録。永続受付後に`202 + jobId` |
| 3：配送 | Outbox → Streams → 配送Event Function → SQS | 提案：jobId・認証済みcustomerIdを配送し、配送済み記録・未配送回復を行う。重複はあり得る |
| 4：生成 | SQS → Worker Event Function → Bedrock | 提案：実行権・attemptIdを確認。入力取得、推論、JSON検証、S3保存、使用量記録、採用結果確定・残量精算 |
| 5：照会 | WPF → CloudFront → Webの`GET /jobs/{jobId}` | 毎回セッションを検証し、Jobs所有者を確認。状態を返し、成功時は採用結果の署名URLを生成して返す |
| 6：取得 | WPF → S3へ直接GET | APIのCloudFront・WAFを通らない。S3は非公開。発行済み署名URLの有効性はセッション失効と別 |

CloudFrontからWPFへの応答は元のHTTP通信を通る。WebがWPFへ別のコールバック接続を行う構成ではない。Bedrock生成は受付Web内では実行せず、Event Workerへ分離する。

## Web案の入口設定

| 部品 | 設定・役割 |
| --- | --- |
| CloudFront | WebのRegional endpointをオリジンにする。HTTPS、必要なHTTPメソッド、全APIのMin／Default／Max TTL＝0 |
| ヘッダー | 全API behaviorのキャッシュポリシーにAuthorizationを含める。Idempotency-Key・Content-Type・必要なクエリ等の転送を確認。viewerのHostは転送しない |
| OAC | Regional endpointでは`sigv4`、署名動作はWeb Functions用の`always-amz-auth`。利用者のBearerを保持し、AWSの署名はCloudFrontが付ける |
| Web endpoint | `IamAuth`。リソースポリシーで`cloudfront.amazonaws.com`の`lambda:InvokeWebFunctionEndpoint`を許可し、`aws:SourceArn`を対象distributionに限定。迂回できる別の許可を作らない |
| WAF | CloudFrontにCLOUDFRONT Web ACLを関連付け。独立した中継サーバーではない。攻撃対策・/auth試行対策・レート制限・誤検知調整 |
| アプリ | 不透明トークン検証、入力検証、所有者認可、顧客別上限、冪等性。OACは顧客認証の代わりにはならない |
| 独自ドメイン | 利用する場合はCloudFrontのalternate domain name、us-east-1のACM証明書、DNSを用意 |

API応答に`Cache-Control: no-store`も設定する。署名なしのendpoint直呼び・別distributionからの呼出しが拒否されること、GET/POST両方でBearerが届くこと、失効後に以前の応答が再利用されないことを検証する。

## リクエストIDとジョブID

CloudFrontが自動付与する`X-Amz-Cf-Id`はHTTP要求1回ごとのID。CloudFrontログの`x-edge-request-id`、WAFログの`requestId`と突合できるようにし、Webアプリでも記録する。アクセスログの有効化・保存先・保持・マスキングは別途設定する。

`jobId`はAPIアプリが発行する生成ジョブのIDで、SQS・Worker・DynamoDB・S3参照まで引き継ぐ。ポーリングごとにCloudFrontのIDは変わるが、対象のjobIdは変わらない。元の受付要求まで追う必要がある場合は、受付のCloudFront IDとjobIdの対応をログ等に残す。冪等キーは再送を同じ操作へ収束させるための別の識別子。

保守キー・平文トークン・Authorization・入力本文・署名URLはログに出さない。

## 提案と未決事項

SQS Fair Queues、Outbox、配送Event Function、入力のS3保存、残量予約・精算、試行別成果物は既存currentにある提案として図示した。これらを採用済みに変更していない。DLQへの移動だけではJobsの失敗確定や予約解放は完了しないため、復旧手順も設計する。

JWT署名鍵は今回の方式では不要。Secrets ManagerをJWT用として図へ残していない。他のサーバー秘密情報の保管先は必要性に応じて決める。専用KMS顧客管理キーを追加しない既存判断は継続する。

停止・失敗・結果不明・再推論の請求、保持期間、受付上限、予算等は[次の作業](../current/次の作業.md)で決める。今回の変更は構成図と案内の追加のみ。

## AWS公式資料

- [Web FunctionオリジンのOAC保護](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-lambda-web.html)
- [Web Function endpointのアクセス制御](https://docs.aws.amazon.com/lambda/latest/dg/web-functions-endpoint-access-control.html)
- [CloudFrontとWAF](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html)
- [CloudFront・WAFのログ相関](https://docs.aws.amazon.com/whitepapers/latest/aws-best-practices-ddos-resiliency/log-correlation-for-ddos-resilient-architectures.html)
