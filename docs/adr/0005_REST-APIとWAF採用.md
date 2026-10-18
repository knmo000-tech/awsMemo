# ADR-0005: REST API + WAFを採用し既存保守キー認証を維持

- **日付**: 2026-10-13
- **ステータス**: **採用（設計確定、未構築）**
- **対象**: API Gateway、AWS WAF、CloudFront

## 背景

複数顧客企業がインターネット経由でAPIを利用する。保守キー認証やトークン課金に関係するAPIのため、HTTPレベルの攻撃、総当たり、過剰リクエストへの多層的な対策が必要。

## 採用する案

**API Gateway REST API（Regional） + AWS WAF** を採用する。REST APIステージにWAFのWeb ACLを直接関連付け、FastAPI + Mangumを使うAPI LambdaへLambdaプロキシ統合で転送する。

WAFのルールはまずCountで正規リクエストへの影響を検証し、管理ルールや§/auth§のIPベースのレートベースルールを段階導入する。

## 採用理由

- AWS WAFをREST APIステージに直接関連付けられ、ネットワーク構成が単純になる。
- 入口で不審なリクエストを検査でき、API Gatewayのアクセスログと合わせて追跡しやすい。
- 顧客向け公開サービスであるため、アプリ認証とは別のHTTP保護層を用意したい。

## 比較・不採用（現時点）の候補

| 案 | 状態 | トレードオフ |
| --- | --- | --- |
| REST API + WAF直接連携 | **採用** | 構成がシンプル。一方、HTTP APIよりAPI Gatewayの料金が高い場合がある |
| HTTP API + CloudFront + WAF | 代替案、未採用 | HTTP API継続が可能。CloudFrontを迂回してHTTP APIを直接呼ぶ経路への対策が必要 |
| HTTP APIへWAFを直接関連付ける | **実現不可として除外** | API Gateway HTTP APIステージにはWAFを直接関連付けできない |
| WAFを使わずアプリ認証だけで防御 | **推奨しない** | 認証前のアクセス負荷・スキャン・総当たりへの保護層が不足 |

## WAFだけでは補えないもの

- 顧客ごとのトークン消費上限や課金制御はFastAPI/サーバー側で実装する。
- 保守キーの保存・検証・短命トークン発行・顧客間のアクセス認可はアプリ側で担う。
- WAFのIPベースレート制限はNAT配下の複数顧客等を区別できない場合がある。

## 保守キー認証・API Gateway APIキーの扱い

- **API Gateway APIキーは使わない**。REST APIの各メソッドで `apiKeyRequired=false` とし、顧客に追加キーを配布しない。
- API Gatewayメソッド認証 `NONE` のLambdaプロキシ統合でAPI Lambda（FastAPI + Mangum）へ転送する。これはAPI Gateway自身が認証を行わないという意味であり、APIが無認証になる設計ではない。
- `POST /auth` は従来の保守キーと顧客名をDynamoDBに照合し、成功時にJWTを発行する。
- `POST /jobs`、`GET /jobs/{jobId}` はJWTを検証し、顧客IDによる所有権・権限を確認する。
- 署名鍵はSecrets Managerに保管する（[ADR-0006](0006-audit-security.md)）。
- REST APIのAPIキーは認証そのものの代用ではないため、未使用でも現在の要件を満たせる。

## 再検討条件

API呼び出し回数、許容コスト、顧客アクセス元、CloudFront導入意義、WAF誤検知リスクを運用設計時に検証する。採用方針は確定済み。トラフィックやインフラ制約が変わったら再評価する。

## 決定の経緯

2026-10-13: WAF直接連携のためREST APIを推奨。後続の確認により、**REST APIでも既存保守キーのDynamoDB照合を変更する必要がなく、別のAPI Gateway APIキー配布も不要**と整理し、REST API + WAFを正式採用。

参考: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

APIキー設定: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-setup-api-keys.html
