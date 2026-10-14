# ADR-0008: Lambda Web Functionsの採否

- **検討日**: 2026-10-15
- **ステータス**: **現時点で不採用（代替候補として保留）**

## 背景

AWSは2026-10-12にLambda Web Functionsを発表した。通常のNode.js WebアプリがHTTPポートで待ち受け、Lambda管理のHTTPSエンドポイント経由で直接リクエストを処理できる。Lambda固有のイベント変換アダプターが不要になり、Express・Honoなどでアプリ内のルーティングを定義できる。

既存構成はWPF → AWS WAF → API Gateway REST API → API Lambda（Python / FastAPI + Mangum）→ 非同期Worker Lambda → Bedrock。結果JSONはS3に保存し、ジョブ状態をポーリングした後に署名付きURLで取得する。

## 比較

| 項目 | 既存構成 | Lambda Web Functions案 |
| --- | --- | --- |
| 公開HTTP入口 | API Gateway REST API | Lambda管理のHTTPSエンドポイント（API Gatewayを省略可能） |
| APIアプリ | Python / FastAPI + Mangum | Node.js / Express・Honoなど（TypeScriptは通常JavaScriptにビルドして実行） |
| ルーティング | FastAPI内のルート（API Gatewayは`ANY /{proxy+}`等で一括転送可能） | Webアプリ内のルート |
| WAF | API Gateway REST APIステージにWeb ACLを関連付け | CloudFront + WAFを前段に配置。OACでWeb Functionsへの直接迂回を制限する構成を検討 |
| 同時実行 | 既存Lambdaのイベントハンドラーモデル | 1実行環境で複数HTTPリクエストを並行処理可能 |
| 料金 | 既存Lambdaの実行時間等 | リクエスト・CPU稼働時間・メモリ保持・転送等に基づく。実測比較が必要 |
| Worker / DynamoDB / S3 | 非同期ジョブ・利用量保存・JSON保管 | 既存方式を維持可能 |

Web FunctionsのHTTPSエンドポイントはAPI Gatewayの全機能を内包するものではない。認証・認可、アプリのルーティング、WAFによる保護や適切な公開制御は別途設計する。

## 決定

**現時点ではLambda Web Functionsへ移行しない。** API入口は引き続き「API Gateway REST API + WAF」、API Lambdaは「Python / FastAPI + Mangum」とする。

### 理由

1. **言語・実装方式**：Web Functionsの初期対応ランタイムはNode.jsのみ。Python / FastAPIをそのまま移すことはできず、API部分のNode.jsへの移植が必要。
2. **入口の保護**：既存構成はREST APIステージにWAFを直接関連付けられる。Web Functionsで同様の保護を行うならCloudFront + WAFとオリジン迂回防止の検討が必要。
3. **現行要件との適合**：APIは認証・ジョブ登録・状態照会の3ルートが中心。既存構成でもFastAPIが複数ルートを扱えるため、API GatewayでルートごとのLambda統合を作る必要はない。
4. **非同期処理との独立性**：Web Functionsに替えてもBedrock処理時間、ジョブの冪等性、利用量記録、請求監査、S3保存やポーリングの設計課題は解消しない。
5. **費用と運用**：初期機能の採用だけでコスト・保守性が改善するとは断定できない。現行構成との測定が必要。

## 再検討条件

- Web FunctionsがPythonに対応し、FastAPI等を大きな移植なしで利用できるようになった場合。
- APIの同時アクセス・レイテンシ・コスト面でWeb Functionsに定量的な利点が確認できた場合。
- Web API部分をTypeScript / Node.jsへ新規実装または移行する方針になった場合。
- WAF・認証・監査要件をCloudFront構成で満たし、運用負荷も許容できる場合。

## 参考（AWS公式）

- [Lambda Web Functions発表（2026-10-12）](https://aws.amazon.com/about-aws/whats-new/2026/10/aws-lambda-web-functions/)
- [Web Functions開発者ガイド](https://docs.aws.amazon.com/lambda/latest/dg/web-functions.html)
- [サポート対象ランタイム](https://docs.aws.amazon.com/lambda/latest/dg/web-functions-runtimes.html)
- [CloudFrontのWeb Functionsオリジン対応](https://aws.amazon.com/about-aws/whats-new/2026/10/cloudfront-lambda-web-functions-origin/)
