# ADR-0011：API入口にEvent Functionsを採用

- 決定日：2026-10-26
- 状態：**利用者による採用決定**。AWS構築・デプロイ・検証完了を表さない。
- 後続対象：ADR-0005、ADR-0008、ADR-0010の入口選定。

## 決定

API入口は**API Gateway Regional REST API＋AWS WAF＋API Lambda Event Function**を採用する。WAFはRESTステージへ直接関連付ける。APIはFastAPI＋Mangumの既存方針を継続し、不透明トークンで認証する。生成処理は別のEvent Workerへ分離する。

利用者から「Web FunctionsではなくEvent Functionsを採用。Web案は検討履歴として残し、currentには載せない」と指定されたため反映する。性能・費用の優位を実測したという判断や、既存Python資産・移植費用を根拠とした判断は追加しない。

## 継続すること・未決のこと

| 論点 | 現在の扱い |
| --- | --- |
| API入口 | Regional REST API＋WAF＋API Event Functionを採用 |
| 認証 | 不透明トークン前提を継続。保存・期限・失効等は詳細設計 |
| 非同期処理 | API／Worker分離を継続 |
| SQS・Outbox・配送Event Function | 推奨・提案のまま。入口選定を採用承認に流用しない |
| 入力S3保存・試行別成果物・残量予約精算 | 提案・業務判断を別に維持 |
| 結果取得 | 非公開S3のJSONを、所有者確認後に署名URLで取得する方針を継続 |
| 監査・暗号化 | 既存方針を継続。追加CMKなし。具体設定・予算・本番化は別判断 |

CloudFront・OACはこの採用入口の必須部品として含めない。新たな追加要件が出た場合は別の判断として記録する。

## 資料の扱い

- currentは採用構成・残る未決事項に統一し、入口の比較ページを外す。
- 比較本文・WEB01〜WEB08は[比較履歴](../比較検討/2026-10-25_REST-APIとWeb-Functionsの構成比較.md)に保存する。
- Web案のSVG・draw.io・シーケンス・編集元は既存パスで保持し、履歴であることを案内する。
- 初版〜rev4のdraw.io・SVGも削除しない。
- 検証では採用入口の保護・認証・正常系・復旧・負荷・運用を確認する。両入口の比較実装は現行作業から外す。

[現在の検討状況](../current/検討状況.md) / [Event入口構成](../current/Event入口構成.md) / [構成設計](../current/構成設計.md)
