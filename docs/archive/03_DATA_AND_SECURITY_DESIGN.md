<!-- 学習用テンプレート（02_design_document_basics/templates/03_DATA_AND_SECURITY_DESIGN.md）を
     Restock Helper の内容で埋めたもの。データ設計部分は decisions_v4.md 8章の要約、
     セキュリティ部分は decisions と開発中のレビュー結果をもとに整理した内容。
     正本は decisions_v4.md であり、本文書と食い違いがある場合は decisions を優先する。 -->

> この文書は2026-10-14に凍結しました。以後は更新しません。内容は、decisions_v7.1 の15章の方針に沿って、spec.md・ADR・開発記録に移します。

# Data and Security Design（データ・セキュリティ設計）

| Item（項目） | Value（値） |
|---|---|
| Document ID（文書ID） | RSH-DATA |
| Version（バージョン） | 0.3 |
| Status（ステータス） | Draft |
| Created Date（作成日） | 2026-08-31 |
| Last Updated（最終更新日） | 2026-10-03 |
| Owner（管理者） | SG-31 |
| Related Documents（関連文書） | README.md / docs/decisions_v4.md |

**v0.2からv0.3の変更点**：参照先をdecisions_v4.md（v3.0本体・v3.1追記・v3.2ドラフトの統合版）に更新。PRGパターン導入に伴うセッション機能・`SECRET_KEY`の扱い、エラー情報の露出対策、サーバー側入力検証、データ修正時の扱いを追記。未決事項にCSRF対策・公開後のアクセス制限等を追加し、TBD-003（`debug=True`）をクローズした。

---

## 1. Purpose（目的）

Restock Helperが扱うデータの種別・保存先・流れと、セキュリティ・個人情報の取り扱い方針を整理する。データ構造そのものの詳細（カラム定義・SQL）は`decisions_v4.md` 8章を正本とし、本文書はそこからの要約と、セキュリティ観点の追加整理を行う。以下、本文中の「decisions」は`decisions_v4.md`を指す。

---

## 2. Scope（対象範囲）

Restock HelperのMVP（トップ案内画面、管理品目の登録・変更・削除、在庫入力、買い物リスト表示、買い物完了、「買ってほしいもの」機能）で扱うデータと、そのセキュリティ対策。

---

## 3. Out of Scope（対象外範囲）

- クラウド公開後の本番運用における監視・アラート体制（デプロイ段階で別途検討）
- 複数ヘルパーによる同時編集時の排他制御（decisions 7-3の前提の通り、MVPでは想定しない）
- 複数世帯対応（decisions 4章。1世帯専用として設計している）

---

## 4. Assumptions（前提条件）

- 個人が特定できる情報（氏名・住所・連絡先等）は扱わない。品目名・数量・メモ内容のみを保存する
- 利用者は、トップ案内画面（`/`）または各画面のURL（高齢者：`/list`、ヘルパー：`/input`・`/items`）からアクセスする（decisions 2章・7-1）
- ログイン機能はMVPでは実装しない（decisions 2章で確定）

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

（詳細はdecisions 8-2「テーブル同士の関係」を参照）

### 5.2 Table Definitions（テーブル定義）

#### items

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | 品目ID |
| name | TEXT | ○ | | 品目名 |
| unit | TEXT | ○ | | 単位 |
| current_stock | INTEGER | ○ | | 現在庫数（0以上。履歴は持たない） |
| created_at | TEXT | ○ | | 登録日時 |
| updated_at | TEXT | ○ | | 更新日時（アプリ側で更新のたびにセット） |

#### consumptions

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | 消費量データID |
| item_id | INTEGER | ○ | FK（items.id） | どの管理品目のデータか |
| consumption | INTEGER | ○ | | 週間消費量（0以上。マイナスは0にクリップして保存） |
| recorded_at | TEXT | ○ | | 記録日時 |

#### shopping_memos

| Column（カラム名） | Type（型） | NOT NULL | PK / FK | Description（説明） |
|---|---|---|---|---|
| id | INTEGER | ○ | PK | メモID |
| text | TEXT | ○ | | 高齢者が入力した内容 |
| created_at | TEXT | ○ | | 追加日時 |

（CREATE TABLE文の全文はdecisions 8-4を参照）

#### 保存しないデータ

移動平均、適正在庫数、補充必要数、買い物リストそのものはDBに保存せず、必要な時点で計算式から求める（decisions 7-3・8-5）。

#### データ修正時の扱い

`/items/<id>/edit`での`current_stock`の直接修正は、`consumptions`への記録を行わない。記録ミスの訂正や、買い物リストに出ていたが実際には買わなかった品目の補正に使う（運用ルールの詳細はdecisions 9-12を参照）。

### 5.3 Data Access and Role Design（データアクセス権限・ロール設計）

| Role Name（ロール名） | Accessible Data / Permitted Operations（アクセス可能なデータ / 操作範囲） |
|---|---|
| 高齢者（`/list`利用者） | shopping_memosの追加・削除、補充が必要な品目の閲覧のみ。items・consumptionsの直接編集はできない |
| ヘルパー（`/input`・`/items`利用者） | itemsの登録・変更・削除、current_stockの更新、consumptionsの新規追加（在庫入力時に自動生成）、shopping_memosの全削除（買い物完了時）。買い物中は`/list`も閲覧する（decisions 7-1） |

**注意**：ログイン機能がないため、上記の役割分担はアプリケーションの**画面設計（URLを役割別に分ける）によって実現**しており、システムが利用者を認証して制御しているわけではない。

### 5.4 Personal and Confidential Data Policy（個人情報・機密データの取り扱い方針）

本文書では対象外。理由：氏名・住所・連絡先等の個人が特定できる情報は保存しない。保存するのは品目名・数量・自由記述メモ（「買ってほしいもの」欄）のみであり、メモ欄の運用上も個人情報の入力は想定しない。

### 5.5 Encryption, Masking, and Logging Policy（暗号化・マスキング・ログ取得方針）

| Type（種別） | Target（対象） | Policy / Method（方式・方針） |
|---|---|---|
| Encryption（暗号化） | 通信経路 | 開発中は対象外（ローカル環境のため）。クラウド公開時はホスティングサービスの標準HTTPS対応に従う（デプロイ段階で確認） |
| Masking（マスキング） | － | 対象外。理由：マスキングが必要な機密データ（パスワード等）を扱わないため |
| Logging（ログ取得） | アクセスログ | Flaskの標準ログ（起動・リクエストの記録）で十分とする。個人情報を含む詳細ログの長期保存は行わない |

### 5.6 Security Design Specifications（セキュリティ設計仕様）

| Type（種別） | Design Specification（設計仕様） |
|---|---|
| Authentication（認証） | 対象外。理由：MVPではログイン機能を実装せず、URLを役割別に分ける簡易方式で代替する（decisions 2章で確定） |
| Authorization（認可） | 上記5.3の通り、URL単位でのアクセス範囲の分離により実現する。システムによる厳密な権限チェックは行わない |
| Access Control（権限管理） | 同上。クラウド公開後のアクセス制限（Basic認証等）は未確定（6章 TBD-005） |
| Communication（通信） | 開発中は対象外。クラウド公開時はHTTPSを利用する（デプロイ段階で確認） |
| Session（セッション） | `/input`のPRGパターン（`flash`による通知メッセージ）のために、Flaskのセッション機能を使用する。セッションに保存するのは一度きりの通知メッセージのみで、画面の表示状態は毎回DBから再計算する（decisions 7-3） |
| Data Storage（データ保存） | SQLite（開発時）／PostgreSQL（公開時、decisions 6章）。DBファイルの保存先フォルダ（`database/`）は起動時に自動作成する。個人情報は保存しないため、保存データ自体の機密性は低い |
| Data Disposal（データ廃棄） | 管理品目削除時、紐づく消費量データを`ON DELETE CASCADE`により物理削除する。SQLiteでは接続ごとに`PRAGMA foreign_keys = ON`が必要なため、`db.py`の接続処理に一本化している（decisions 3-7・8-4・8-6） |
| Personal Data Protection（個人情報保護） | 対象外。理由：5.4の通り個人情報を扱わない |
| 入力値の検証（SQLインジェクション対策） | SQL文はプレースホルダ（`?`）を使い、文字列を直接組み込まない。マイナス値等の不正な在庫数はアプリ側で警告・保存不可とし、DB側にもCHECK制約を設けて二重に保護する。品目名・単位はサーバー側でも入力検証を行う |
| エラー情報の露出対策 | Flaskは`debug=False`をデフォルトとし、環境変数`FLASK_DEBUG`で切り替える。DBエラー発生時は、内部の詳細を画面に出さず、固定のメッセージを表示する |
| 二重送信対策 | PRGパターンにより、リロード・戻るボタンによる再送信を防ぐ。保存・買い物完了ボタンは、確認ダイアログでOKした後に無効化し、連打を防ぐ（decisions 7-3・9-6・14-1） |
| 秘密情報の管理 | セッションの署名に使う`SECRET_KEY`は、コードに直書きせず環境変数から読み込む。未設定時は開発用のデフォルト値を使うため、本番運用時は必ず推測されにくい値を環境変数に設定する（6章 TBD-004）。`.env`は`.gitignore`で除外する |

---

## 6. Open Issues（未決事項）

| ID | Open Issue（未決事項） | Owner（担当者） | Due Date（期限） | Status（ステータス） |
|---|---|---|---|---|
| TBD-001 | クラウド公開時のHTTPS対応方法の確認 | SG-31 | デプロイ段階 | Open |
| TBD-002 | SQLインジェクション対策（プレースホルダ使用）が全SQL文で守られているかのレビュー | SG-31 | デプロイ前 | Open（要確認：レビュー済みであればClosedに変更） |
| TBD-003 | Flaskの`debug=True`を、デプロイ前に`False`へ変更する（ruff `S201`で検出済み） | SG-31 | － | Closed（`debug=False`をデフォルトとし、`FLASK_DEBUG`で切替可能にした） |
| TBD-004 | 本番用`SECRET_KEY`の設定方法（ホスティングサービスの環境変数設定）。未設定のまま開発用の値で起動しないようにする仕組みの要否も含む | SG-31 | デプロイ段階 | Open |
| TBD-005 | CSRF対策（Flask-WTFの導入、全フォームへのトークン追加）と、クラウド公開後のアクセス制限（Basic認証等）の方針決定 | SG-31 | デプロイ前 | Open |
| TBD-006 | `.gitignore`の除外対象の確認：現在の仮想環境`.venv/`、DBファイル（`*.db`）が除外されているか。Public化前には、過去のコミットにDBファイルが含まれていないかも確認する（decisions 11章） | SG-31 | Public化前 | Open（現在の状態は確認済み：`.venv/`・`*.db`とも除外され、Git管理下にもない（2026-10-03）。過去コミットの履歴確認のみ残る） |

---

## 7. Handoff to Detail Design（詳細設計への引き継ぎ）

- 認証・認可を実装しない設計であるため、URLが第三者に知られた場合、役割を超えた画面（例：高齢者が`/input`にアクセスする等）へのアクセスを技術的には防げない。これはMVPとして意図的に許容している制約であり、README等に明記すること（decisions 2章参照）。クラウド公開後はURLを知っていれば誰でも操作できる状態になるため、公開前にTBD-005の方針を決めること
- 実装時、SQL文は必ずプレースホルダを使うこと。`f文字列`や`+`によるSQL文の組み立ては行わないこと
- `SECRET_KEY`などの秘密情報は、コード・リポジトリに含めないこと
