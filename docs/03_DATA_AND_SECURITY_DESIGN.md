<!-- 学習用テンプレート（02_design_document_basics/templates/03_DATA_AND_SECURITY_DESIGN.md）を
     Restock Helper の内容で埋めたもの。データ設計部分は decisions_v2.1.md 8章の要約、
     セキュリティ部分は本チャットで新たに整理した内容。 -->

# Data and Security Design（データ・セキュリティ設計）

| Item（項目） | Value（値） |
|---|---|
| Document ID（文書ID） | RSH-DATA |
| Version（バージョン） | 0.1 |
| Status（ステータス） | Draft |
| Created Date（作成日） | 2026-08-31 |
| Last Updated（最終更新日） | 2026-08-31 |
| Owner（管理者） | SG-31 |
| Related Documents（関連文書） | README.md / docs/decisions_v2.1.md |

---

## 1. Purpose（目的）

Restock Helperが扱うデータの種別・保存先・流れと、セキュリティ・個人情報の取り扱い方針を整理する。データ構造そのものの詳細（カラム定義・SQL）は`decisions_v2.1.md`8章を正本とし、本文書はそこからの要約と、セキュリティ観点の追加整理を行う。

---

## 2. Scope（対象範囲）

Restock HelperのMVP（管理品目の登録・在庫入力・買い物リスト表示・買い物完了・「買ってほしいもの」機能）で扱うデータと、そのセキュリティ対策。

---

## 3. Out of Scope（対象外範囲）

- クラウド公開後の本番運用における監視・アラート体制（デプロイ段階で別途検討）
- 複数ヘルパーによる同時編集時の排他制御（7-3の前提の通り、MVPでは想定しない）

---

## 4. Assumptions（前提条件）

- 個人が特定できる情報（氏名・住所・連絡先等）は扱わない。品目名・数量・メモ内容のみを保存する
- 高齢者・ヘルパーは、それぞれ専用のURL（`/list`、`/input`）を知っている前提で利用する（2章）
- ログイン機能はMVPでは実装しない（2章で確定）

---

## 5. Definition Details（定義内容）

### 5.1 Entity Definition and ER Diagram（エンティティ定義・ER図）

| Entity Name（エンティティ名） | Description（説明） |
|---|---|
| items（管理品目） | 継続的に在庫管理する商品。現在庫数を1件につき1つだけ保持 |
| consumptions（消費量データ） | 毎週の入力から算出された週間消費量の履歴 |
| shopping_memos（買ってほしいもの） | 高齢者が追加する、今回限りの自由メモ |

```
items（管理品目） 1 ── 多 consumptions（消費量データ）
shopping_memos（買ってほしいもの） … 独立（他エンティティと関連付けしない）
```

（詳細は`decisions_v2.1.md` 8-2「テーブル同士の関係」を参照）

### 5.2 Table Definitions（テーブル定義）

#### items

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | 品目ID |
| name | TEXT | ○ | | 品目名 |
| unit | TEXT | ○ | | 単位 |
| current_stock | INTEGER | ○ | | 現在庫数（0以上。履歴は持たない） |
| created_at | TEXT | ○ | | 登録日時 |
| updated_at | TEXT | ○ | | 更新日時 |

#### consumptions

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | 消費量データID |
| item_id | INTEGER | ○ | FK（items.id） | どの管理品目のデータか |
| consumption | INTEGER | ○ | | 週間消費量（0以上） |
| recorded_at | TEXT | ○ | | 記録日時 |

#### shopping_memos

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | メモID |
| text | TEXT | ○ | | 高齢者が入力した内容 |
| created_at | TEXT | ○ | | 追加日時 |

（CREATE TABLE文の全文は`decisions_v2.1.md` 8-4を参照）

### 5.3 Data Access and Role Design（データアクセス権限・ロール設計）

| Role Name（ロール名） | Accessible Data / Permitted Operations（アクセス可能なデータ / 操作範囲） |
|---|---|
| 高齢者（`/list`利用者） | shopping_memosの追加・削除、items・consumptionsの補充必要数の閲覧のみ。items・consumptionsの直接編集はできない |
| ヘルパー（`/input`・`/items`利用者） | itemsの登録・変更・削除、current_stockの更新、consumptionsの新規追加（間接的に自動生成）、shopping_memosの削除（買い物完了時） |

**注意**：ログイン機能がないため、上記の役割分担はアプリケーションの**画面設計（URLを役割別に分ける）によって実現**しており、システムが利用者を認証して制御しているわけではない（4-1参照）。

### 5.4 Personal and Confidential Data Policy（個人情報・機密データの取り扱い方針）

本文書では対象外。理由：氏名・住所・連絡先等の個人が特定できる情報は保存しない。保存するのは品目名・数量・自由記述メモ（「買ってほしいもの」欄）のみであり、メモ欄の運用上も個人情報の入力は想定しない。

### 5.5 Encryption, Masking, and Logging Policy（暗号化・マスキング・ログ取得方針）

| Type（種別） | Target（対象） | Policy / Method（方式・方針） |
|---|---|---|
| Encryption（暗号化） | 通信経路 | 開発中は対象外（ローカル環境のため）。クラウド公開時はホスティングサービスの標準HTTPS対応に従う（⑦デプロイ段階で確認） |
| Masking（マスキング） | － | 対象外。理由：マスキングが必要な機密データ（パスワード等）を扱わないため |
| Logging（ログ取得） | アクセスログ | Flaskの標準ログ（起動・リクエストの記録）で十分とする。個人情報を含む詳細ログの長期保存は行わない |

### 5.6 Security Design Specifications（セキュリティ設計仕様）

| Type（種別） | Design Specification（設計仕様） |
|---|---|
| Authentication（認証） | 対象外。理由：MVPではログイン機能を実装せず、URLを役割別に分ける簡易方式で代替する（2章で確定） |
| Authorization（認可） | 上記5.3の通り、URL単位でのアクセス範囲の分離により実現する。システムによる厳密な権限チェックは行わない |
| Access Control（権限管理） | 同上 |
| Communication（通信） | 開発中は対象外。クラウド公開時はHTTPSを利用する（デプロイ段階で確認） |
| Data Storage（データ保存） | SQLite（開発時）／PostgreSQL（公開時）。個人情報は保存しないため、保存データ自体の機密性は低い |
| Data Disposal（データ廃棄） | 管理品目削除時、紐づく消費量データを`ON DELETE CASCADE`により物理削除する（decisions_v2.1.md 3-7・8-4参照） |
| Personal Data Protection（個人情報保護） | 対象外。理由：5.4の通り個人情報を扱わない |
| 入力値の検証（SQLインジェクション対策） | 実装時、SQL文はプレースホルダ（`?`）を使い、文字列を直接組み込まない。マイナス値等の不正な入力はアプリ側でも警告・保存不可とする（decisions_v2.1.md ユースケース①、3-2） |
| 秘密情報の管理 | APIキー・パスワード等は現時点で使用しない。将来使用する場合は`.env`に分離し、`.gitignore`で除外する（プロジェクトの基本方針に基づく） |

---

## 6. Open Issues（未決事項）

| ID | Open Issue（未決事項） | Owner（担当者） | Due Date（期限） | Status（ステータス） |
|---|---|---|---|---|
| TBD-001 | クラウド公開時のHTTPS対応方法の確認 | SG-31 | ⑦デプロイ段階 | Open |
| TBD-002 | SQLインジェクション対策（プレースホルダ使用）の実装時レビュー | SG-31 | ⑤実装段階 | Open |

---

## 7. Handoff to Detail Design（詳細設計への引き継ぎ）

- 認証・認可を実装しない設計であるため、URLが第三者に知られた場合、役割を超えた画面（例：高齢者が`/input`にアクセスする等）へのアクセスを技術的には防げない。これはMVPとして意図的に許容している制約であり、README等に明記すること（2章参照）
- 実装時、SQL文は必ずプレースホルダを使うこと。`f文字列`や`+`によるSQL文の組み立ては行わないこと
