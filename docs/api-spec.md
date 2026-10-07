# API仕様書（ドラフト）

API Gateway HTTP API + 1つのAPI Lambdaを想定。リクエストとレスポンスはJSON（UTF-8）。`/auth` 以外は `Authorization: Bearer <accessToken>` が必要です。

| HTTP | エンドポイント | 成功コード | 役割 |
| --- | --- | --- | --- |
| POST | `/auth` | 200 | 保守キー・顧客名照合、トークン発行 |
| POST | `/jobs` | 202 | ジョブ登録、Worker非同期起動 |
| GET | `/jobs/{jobId}` | 200 | 状態取得、完了時にCSVダウンロードURL発行 |

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

## POST /jobs

Request:
```json
{"inputText":"CSV化したい文章","outputFormat":"csv"}
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
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"SUCCEEDED","result":{"fileName":"result.csv","downloadUrl":"https://example.invalid/presigned-url","urlExpiresIn":300}}
```
Response 200（失敗）:
```json
{"jobId":"c7c5c92c-0d66-4d7d-8409-9dd6a1c4c8f1","status":"FAILED","error":{"code":"GENERATION_FAILED","message":"CSV生成に失敗しました"}}
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
- ポーリング間隔、入力長、タイムアウト、CSV形式、ダウンロードURL期限は要確定。

関連: [構成設計](architecture.md) / [シーケンス](sequence.md)
