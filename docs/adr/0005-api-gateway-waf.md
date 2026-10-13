# ADR-0005: 公開APIの入口はREST API + WAFを推奨

- **日付**: 2026-10-13
- **ステータス**: **検討中**（採用未確定）
- **対象**: API Gateway、AWS WAF、CloudFront

## 背景

複数顧客企業がインターネット経由でAPIを利用する。保守キー認証やトークン課金に関係するAPIのため、HTTPレベルの攻撃、総当たり、過剰リクエストへの多層的な対策が必要。

## 推奨する案

**API Gateway REST API（Regional） + AWS WAF** を第一候補とする。REST APIステージにWAFのWeb ACLを直接関連付け、FastAPI + Mangumを使うAPI LambdaへLambdaプロキシ統合で転送する。

WAFのルールはまずCountで正規リクエストへの影響を検証し、管理ルールや§/auth§のIPベースのレートベースルールを段階導入する。

## 推奨理由

- AWS WAFをREST APIステージに直接関連付けられ、ネットワーク構成が単純になる。
- 入口で不審なリクエストを検査でき、API Gatewayのアクセスログと合わせて追跡しやすい。
- 顧客向け公開サービスであるため、アプリ認証とは別のHTTP保護層を用意したい。

## 比較・不採用（現時点）の候補

| 案 | 状態 | トレードオフ |
| --- | --- | --- |
| REST API + WAF直接連携 | **推奨、未確定** | 構成がシンプル。一方、HTTP APIよりAPI Gatewayの料金が高い場合がある |
| HTTP API + CloudFront + WAF | 代替案、未採用 | HTTP API継続が可能。CloudFrontを迂回してHTTP APIを直接呼ぶ経路への対策が必要 |
| HTTP APIへWAFを直接関連付ける | **実現不可として除外** | API Gateway HTTP APIステージにはWAFを直接関連付けできない |
| WAFを使わずアプリ認証だけで防御 | **推奨しない** | 認証前のアクセス負荷・スキャン・総当たりへの保護層が不足 |

## WAFだけでは補えないもの

- 顧客ごとのトークン消費上限や課金制御はFastAPI/サーバー側で実装する。
- 保守キーの保存・検証・短命トークン発行・顧客間のアクセス認可はアプリ側で担う。
- WAFのIPベースレート制限はNAT配下の複数顧客等を区別できない場合がある。

## 確定前の確認と再検討条件

API呼び出し回数、許容コスト、顧客アクセス元、CloudFront導入意義、誤検知リスクを検証したうえでREST API案を確定する。トラフィックやインフラ制約が変わったら再評価する。

参考: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
