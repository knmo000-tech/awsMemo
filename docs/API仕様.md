# API仕様

API Gateway REST API → FastAPI（Mangum）。JSONリクエスト／レスポンス。**API Gateway独自のAPIキーは不要**。

WPFは`POST /auth`で取得したJWTをメモリに保持し、有効期限内は`POST /jobs`と`GET /jobs/{jobId}`で再利用する。未取得・期限切れ時（または401応答時）は再認証する。API LambdaはBearer JWTを毎リクエスト検証する。

| メソッド | パス | 認証 | 成功 | 用途 |
| --- | --- | --- | --- | --- |
| `POST` | `/auth` | 保守キー＋顧客名 | 200 | JWT発行 |
| `POST` | `/jobs` | Bearer JWT | 202 | 非同期ジョブ登録 |
| `GET` | `/jobs/{jobId}` | Bearer JWT | 200 | 状態・結果URL取得 |

## POST /auth

Request:
```json
{"maintenanceKey":"EXAMPLE-KEY","customerName":"サンプル株式会社"}
```

Response `200`:
```json
{"accessToken":"example-token","tokenType":"Bearer","expiresIn":900,"customerId":"customer-001"}
```

## POST /jobs

Request:
```json
{"inputText":"JSON生成に用いる文章","outputFormat":"json"}
```

Response `202`:
```json
{"jobId":"example-job-id","status":"QUEUED","statusUrl":"/jobs/example-job-id"}
```

## GET /jobs/{jobId}

Response `200`（処理中）:
```json
{"jobId":"example-job-id","status":"RUNNING","result":null}
```

Response `200`（成功）:
```json
{"jobId":"example-job-id","status":"SUCCEEDED","result":{"fileName":"result.json","contentType":"application/json","downloadUrl":"https://example.invalid/presigned-url","urlExpiresIn":300}}
```

Response `200`（失敗）:
```json
{"jobId":"example-job-id","status":"FAILED","error":{"code":"GENERATION_FAILED","message":"JSON生成に失敗しました"}}
```

署名付きURLはジョブ所有者を確認してから発行。クライアントはS3からJSONを直接ダウンロードする。

## エラー

共通形式:
```json
{"error":{"code":"UNAUTHORIZED","message":"認証が必要です"},"requestId":"example-request-id"}
```

| HTTP | コード例 | 用途 |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | 不正な入力 |
| 401 | `INVALID_CREDENTIALS`, `UNAUTHORIZED` | 認証失敗・JWT無効 |
| 404 | `JOB_NOT_FOUND` | 対象ジョブなし／他顧客のジョブ |
| 413 | `PAYLOAD_TOO_LARGE` | 入力上限超過 |
| 429 | `RATE_LIMITED` | リクエスト制限 |
| 500・503 | `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE` | サーバーエラー |

FastAPI標準の入力検証エラーは422。400に統一するなら例外ハンドラーを実装する。WAF／API Gateway由来のエラー形式は別途調整が必要。

## 未確定パラメータ

JWTの有効期限・署名方式、入力上限、JSONスキーマ、ジョブのポーリング間隔、署名URLの期限、エラー形式の統一方針。

## 2026-10-19：ジョブ受付の冪等性（検討案）

`POST /jobs`ではボタン連打や通信リトライによる重複作成を防ぐため、`Idempotency-Key`等の導入を推奨。同一顧客・同一キーに対して同一`jobId`を返す設計とし、DynamoDBの条件付き書き込みで実現する。SQSを採用する場合はDynamoDB登録とSQS送信の一部失敗を回復する仕組みも必要。

- 本項は**仕様追加候補であり、必須ヘッダーや保持期間は未確定**。
- SQSの`MessageGroupId`にサーバー側で確定した`customerId`を指定し、企業別の公平性を補助する。
- 202 Acceptedは受付済みを表すもので、生成成功や完了を意味しない。

