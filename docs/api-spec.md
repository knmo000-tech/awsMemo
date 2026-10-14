# API仕様書（ドラフト）

> **更新方針（2026-10-13）**: API実装にFastAPI + Mangumを採用する。API Gatewayは **REST API + AWS WAFを推奨案** とし、採用決定まではHTTP APIからの変更を「検討中」として扱う。公開エンドポイントのパスとJSON例は維持する。OpenAPIはFastAPIから生成可能だが、本番で`/docs`や`/openapi.json`を公開するかは別途決める。


API Gateway REST API + AWS WAFを推奨案とする（API Gateway種類は検討中）。FastAPI + Mangumを載せた1つのAPI Lambdaを想定。リクエストとレスポンスはJSON（UTF-8）。`/auth` 以外は `Authorization: Bearer <accessToken>` が必要です。

| HTTP | エンドポイント | 成功コード | 役割 |
| --- | --- | --- | --- |
| POST | `/auth` | 200 | 保守キー・顧客名照合、トークン発行 |
| POST | `/jobs` | 202 | ジョブ登録、Worker非同期起動 |
| GET | `/jobs/{jobId}` | 200 | 状態取得、完了時にJSONダウンロードURL発行 |

## POST /auth

Request:
```json
{"maintenanceKey":"EXAMPLE-KEY","customerName":"サンプル株式会社"}
```
Response 200:
```json
{"accessToken":"example-token","tokenType":"Bearer","expiresIn":900,"customerId":"customer-001"}
```
エラー: 400 `VALIDATION_ERROR`、401 `INVALID_CREDENTIALS`、429 `RATE_LIMITED`、500 `INTERNAL_ERROR`。


> **2026-10-15：生成物をJSONに変更。** `POST /jobs` は非同期受付（202）、`GET /jobs/{jobId}` は引き続きポーリングで状態／署名付きURLを返す。S3に保存するファイルは `result.json`（`application/json`）を想定。

## POST /jobs

Request:
```json
{"inputText":"JSON生成に用いる文章","outputFormat":"json"}
```
Response 202:
```json
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"QUEUED","statusUrl":"/jobs/c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1"}
```
エラー: 400 `VALIDATION_ERROR`、401 `UNAUTHORIZED`、413 `PAYLOAD_TOO_LARGE`、429 `RATE_LIMITED`、500 `INTERNAL_ERROR`、503 `SERVICE_UNAVAILABLE`。

## GET /jobs/{jobId}

Response 200（処理中）:
```json
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"RUNNING","result":null}
```
Response 200（成功）:
```json
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"SUCCEEDED","result":{"fileName":"result.json","contentType":"application/json","downloadUrl":"https://example.invalid/presigned-url","urlExpiresIn":300}}
```
Response 200（失敗）:
```json
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"FAILED","error":{"code":"GENERATION_FAILED","message":"JSON生成に失敗しました"}}
```
エラー: 400 `VALIDATION_ERROR`、401 `UNAUTHORIZED`、404 `JOB_NOT_FOUND`（別顧客ジョブを含む）、429 `RATE_LIMITED`、500 `INTERNAL_ERROR`。

共通エラー形式:
```json
{"error":{"code":"UNAUTHORIZED","message":"認証が必要です"},"requestId":"example-request-id"}
```

## 要実装・要検討

- JWT等のトークン署名と有効期限検証、顧客単位のジョブ認可。キーや秘密情報をログに出さない。
- ジョブの冪等性、非同期起動失敗への補償、Workerの再試行と状態整合性。
- API Gatewayのエラーも共通形式に寄せる場合は追加設定が必要。
- ポーリング間隔、入力長、タイムアウト、JSON形式、ダウンロードURL期限は要確定。

関連: [構成設計](architecture.md) / [シーケンス](sequence.md)


## FastAPIとAPI Gatewayの責務

- API Gateway: HTTPS受付、WAFとの連携（REST API採用時）、アクセスログ、スロットリング、Lambda呼び出し。
- FastAPI: ルーティング、Pydanticの型検証、Bearerトークンの**実際の検証処理**、顧客の認可、APIレスポンス。
- Mangum: API GatewayイベントとFastAPIのASGIリクエスト/レスポンスの変換。
- Lambda: FastAPIアプリを`handler = Mangum(app)`で実行。ZIP/コンテナにFastAPI/Mangumなどの依存関係を同梱する。
- 既定のFastAPIバリデーションエラーはHTTP 422・独自JSON形式。**本仕様の400/共通エラー形式に合わせるにはRequestValidationError用の例外ハンドラーが必要**。422を採用するかも決定する。
- AWS WAF/API Gateway側が生成する403/429/5xxはFastAPIの例外ハンドラーを通らないため、共通エラー形式を保証するにはGateway Responses等の設定やクライアント側の別処理が必要。
- `/auth` の保守キーは認証材料であるため、API Gatewayアクセスログ、WAFログ、FastAPIログに出力しない。入力本文、Bearerトークン、署名付きURLも秘匿する。

詳細: [セキュリティ・監査設計](security.md) / [構成設計](architecture.md)
