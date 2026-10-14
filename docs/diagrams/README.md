# AWS構成図

| 版 | 編集用 | プレビュー |
| --- | --- | --- |
| **rev4（JSON）** | [draw.io（2ページ）](aws-architecture-rev4.drawio) | [業務処理](aws-architecture-rev4-business.svg) / [セキュリティ・監査](aws-architecture-rev4-security.svg) |
| rev3（CSV） | [draw.io](aws-architecture-rev3.drawio) | [業務処理](aws-architecture-rev3-business.svg) / [セキュリティ・監査](aws-architecture-rev3-security.svg) |
| rev2 | [draw.io](aws-architecture-rev2.drawio) | [SVG](aws-architecture-rev2.svg) |
| rev1 | [draw.io](aws-architecture-rev1.drawio) | [SVG](aws-architecture-rev1.svg) |

## 業務処理

![業務処理・データフロー](aws-architecture-rev4-business.svg)

## セキュリティ・監査

![セキュリティ・監査](aws-architecture-rev4-security.svg)

**図の読み方**：実線は処理経路、破線は補助的な連携・検討対象。DynamoDBの`UsageEvents`は物理分割未決定。WAFはREST APIステージに関連付けるWeb ACLを前段として表現。

AWSサービスアイコン：[AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)（[SVG素材カタログ](https://github.com/phergoualch/aws-icons)）。
