# ADR-0008: Lambda Web Functionsと通常Lambdaの比較

- **初回検討**：2026-10-15
- **再評価**：2026-10-19（既存Python/FastAPI資産を前提から除外）
- **ステータス**：Web Functions不採用（現時点）／REST API + WAF + Event Functionsを第一候補

**2026-10-20追記**：CloudFront OAC＋IamAuthによるWeb Functionsのオリジン保護と、10秒ポーリング・月140万API要求の楽観/標準/悲観料金モデルを再評価。正式な採否変更はなく、実測前の参考比較。詳細は[2026-10-20の比較資料](../比較検討/2026-10-20_REST-APIとWeb-Functions採用比較.md)を参照。

## 比較の前提
100企業がWPFのボタン押下でジョブを1件ずつ作成。月間1万・10万・20万ジョブ、20営業日×8時間を仮定する。非同期方式は維持。S3に最大約1MBの生成JSON、DynamoDBに顧客・ジョブ・使用量、Worker LambdaからBedrock呼び出し。SQS Fair Queuesは導入推奨の検討候補。

## 実行モデル・機能・運用差

| 項目 | REST API + 通常Lambda | HTTP API + 通常Lambda | Web Functions |
| --- | --- | --- | --- |
| HTTP入口 | API Gateway REST | API Gateway HTTP | HTTPSエンドポイント内蔵 |
| WAF必須 | **RESTステージにWeb ACL直接** | CloudFront + WAF | CloudFront + WAF |
| 迂回経路対策 | REST側で直接防御 | CloudFront迂回でHTTP API直接呼出しされないよう追加設計 | IAM認証 + CloudFront OACなどを検討 |
| 実行単位 | ハンドラー。1環境は基本1リクエスト | 同左 | HTTPサーバー。1環境で複数同時リクエスト |
| 費用の構造 | 要求数＋実行時間/メモリ | 同左（Gatewayの要求単価が低い） | 要求数＋CPU実働時間＋環境メモリ滞在時間 |
| 認証/制限 | API Gateway機能＋アプリ | API Gateway機能＋アプリ | WebアプリやCloudFront側の実装が必要 |
| ストリーミング | 統合方式に制約 | 統合方式に制約 | 得意だが今回の非同期要件では主目的でない |
| SQS/Worker/DynamoDB/S3 | 共通で維持 | 共通で維持 | 共通で維持 |

### Web Functionsのメリット
1. 一般的なNode.js Webサーバー、Express/Fastify/Hono等をHTTPサーバーのまま動かせる。
2. 1つの実行環境内で複数HTTP要求を処理可能。DynamoDBアクセス等I/O待ちの多いAPIを効率化し得る。
3. CPU稼働時間とメモリ環境時間を分けた課金により、負荷特性によって安価になり得る。
4. 長時間HTTP応答・ストリーミングの実装と相性がよい。

### Web Functionsのデメリット
1. API Gateway REST APIの管理機能がそのまま使えるわけではなく、JWT認証・顧客別認可・流量制限・監視などの実装範囲が変わる。
2. WAF必須ならCloudFrontやオリジン保護を追加する必要があり、構成全体が簡潔になるとは限らない。
3. 環境のメモリ稼働時間次第で安くならない。
4. 1プロセスで複数企業を同時処理するため、JWTや顧客IDをグローバルな可変状態に置かないよう注意。
5. 2026-10-19時点でWeb Functionsの初期対応はNode.jsのみ。新サービスにつき運用知見が少ない。ただし今回の採否判断で移植費用は考慮しない。

## 非同期システムでの境界
Web Functionsに変えてもS3を廃止できるわけではない。HTTP受付とジョブ・生成物の永続保存は別問題。今回の非同期ジョブ構成、請求監査、冪等性、SQS流量制御、ポーリングは引き続き必要。

## 結論と見直し
**REST API（Regional） + WAF直接連携 + Event Functionsを第一候補として維持する。** WAFを必須とする100社向けシステムでは、CloudFrontの追加とWAF迂回対策の管理を回避できる点が強い。Web Functionsの性能・価格メリットは実測されていない。

再検討：HTTP要求数の大幅増加、実測p95・エラー率・費用の優位、ストリーミング追加、既存CloudFront基盤の流用など。

[机上試算・詳細比較](../比較検討/2026-10-19_非同期Bedrock基盤とAPI方式の比較.md) / [SQS Fair Queues検討](0009_SQS公平キュー導入検討.md)。

### AWS公式
- https://docs.aws.amazon.com/lambda/latest/dg/web-functions.html
- https://aws.amazon.com/lambda/pricing/
- https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fair-queues.html
