# Architecture Design（アーキテクチャ設計）

<!-- Document Info（文書情報） -->
| Item（項目） | Value（値） |
|---|---|
| Document ID（文書ID） | RH-ARCH |
| Version（バージョン） | 0.1 |
| Status（ステータス） | Draft |
| Created Date（作成日） | 2026-10-14 |
| Last Updated（最終更新日） | 2026-10-14 |
| Owner（管理者） | SG-31 |
| Related Documents（関連文書） | [README.md](../README.md) / [02_REQUIREMENTS_DEFINITION.md](./02_REQUIREMENTS_DEFINITION.md) / [03_DATA_AND_SECURITY_DESIGN.md](./03_DATA_AND_SECURITY_DESIGN.md) / [06_OPERATION_AND_HANDOFF.md](./06_OPERATION_AND_HANDOFF.md) |

---

## Table of Contents（目次）

1. [Purpose（目的）](#1-purpose目的)
2. [Scope（対象範囲）](#2-scope対象範囲)
3. [Out of Scope（対象外範囲）](#3-out-of-scope対象外範囲)
4. [Assumptions（前提条件）](#4-assumptions前提条件)
5. [Definition Details（定義内容）](#5-definition-details定義内容)
6. [Open Issues（未決事項）](#6-open-issues未決事項)
7. [Handoff to Detail Design（詳細設計への引き継ぎ）](#7-handoff-to-detail-design詳細設計への引き継ぎ)

---

## 1. Purpose（目的）

Restock Helper を構成する部品と、そのつながり、使う技術と選んだ理由、開発・本番の環境を定義する。

---

## 2. Scope（対象範囲）

- アプリ（Flask）とDB（PostgreSQL）の構成と、各部品の責務
- 公開先（Vercel・Neon）と、開発用のPC
- 外部のサービスとのつながり

---

## 3. Out of Scope（対象外範囲）

- テーブルの構造・ログインの仕組み・秘密の値の扱いは 03、画面と操作は 04、確認の方法・公開の手順・障害のときの対応は 06 で扱う

---

## 4. Assumptions（前提条件）

- 1世帯専用で、利用者は2人、データは数十件の規模とする（02 の 5.5）
- 費用をかけず、各サービスの無料プランの範囲で動かす
- 高齢者とヘルパーが別々のスマートフォンから同じデータを見るため、データはサーバー側に1か所で持つ

---

## 5. Definition Details（定義内容）

### 5.1 System Architecture Diagram（システム構成図）

```mermaid
flowchart LR
  subgraph 利用者
    E[高齢者のスマートフォン]
    H[ヘルパーのスマートフォン]
  end
  subgraph Vercel（シンガポール）
    A[Flask アプリ]
  end
  subgraph Neon（シンガポール）
    D[(PostgreSQL)]
  end
  E -->|HTTPS| A
  H -->|HTTPS| A
  A -->|接続先は環境変数で指定| D
  G[GitHub] -->|main は本番<br>ほかのブランチはプレビュー| A
```

- 画面はサーバー側で作り、ブラウザに返す。ブラウザの中で動く処理は、確認ダイアログ・変更した行の色付け・ボタンの無効化だけとする
- アプリはデータを持たず、すべて Neon の DB に保存する

### 5.2 Technology Stack and Rationale（技術スタック・採用理由）

| Type（種別） | Technology（採用技術） | Version（バージョン） | Rationale（採用理由） |
|---|---|---|---|
| Language（言語） | Python | 3.13 | ・Python と Flask の学習を兼ねるため<br>・Vercel の初期値は 3.12 のため、使う版を指定する |
| Framework（フレームワーク） | Flask | 3.1.3 | ・画面数が少ない小さな Web アプリを、少ない部品で作れるため |
| Database（DB） | PostgreSQL | 18 | ・2人が別の端末から同じデータを使うため、アプリと別に動くサーバー型のDBとする<br>・Vercel ではファイルを保存し続けられないため、ファイル型のDB（SQLite）からは移行した<br>・開発用のPCも同じ PostgreSQL にそろえ、本番で初めて誤りが見つかるのを防ぐ |
| Infrastructure（インフラ） | Vercel（Hobby プラン） | ― | ・無料で、長いスリープ（起動の待ち）がない<br>・Flask を設定なしで扱える<br>・保護されたプレビューで、変更を本番の前に確かめられる<br>・講師に相談できる |
| Infrastructure（インフラ） | Neon（Free プラン） | ― | ・無料で期限がなく、クレジットカードが要らない<br>・使われないと休止するが、次の接続で自動的に再開する |
| Other（その他） | psycopg | 3.3.6 | ・PostgreSQL への接続に使う<br>・ORM は使わず SQL を直接書く。Python と SQL と DB の関係を自分の手で理解するため |
| Other（その他） | Flask-WTF | 1.3.0 | ・不正なフォーム送信を防ぐため（CSRF対策。03） |
| Other（その他） | python-dotenv | 1.2.4 | ・ローカルで `.env` から環境変数を読むため。本番では使わない |
| Other（その他） | pytest・ruff | pytest 9.1.1 | ・計算と入力チェックの単体テスト、コードの静的解析のため |

- 公開先は、Render・Railway・Koyeb・PythonAnywhere・Supabase（DB）とも比べて選んだ。比較の範囲と結果は [decisions_v7.1](./archive/decisions_v7.1.md) の 6章
- Vercel と Neon は、どちらもシンガポールにそろえる。このアプリは品目ごとに DB に問い合わせるため、アプリと DB の距離が応答の速さに大きく影響する。Neon には東京がなく、シンガポールが最も近い

### 5.3 Module Structure and Layer Design（モジュール構成・レイヤー設計）

| Component（コンポーネント） | Responsibility（責務） |
|---|---|
| app.py | ・アプリの起動と、起動時の確認（秘密の値・DB が使えないときは起動しない）<br>・ログイン・ログアウトと、全画面のログイン確認<br>・CSRF対策、404 と CSRF のエラー画面<br>・テーブルの作成（なければ作る）と、各画面の部品の登録 |
| routes/items.py | ・管理品目の一覧・登録・変更・削除（SCR-004・005） |
| routes/stock.py | ・在庫入力と、消費量の記録（SCR-003） |
| routes/shopping.py | ・買い物リストと「買ってほしいもの」（SCR-002）<br>・買い物完了 |
| calculations.py | ・補充する数の計算。DB も Flask も使わない |
| validation.py | ・品目と在庫数の入力チェック。DB も Flask も使わない |
| db.py | ・DB への接続（接続先は環境変数 `DATABASE_URL`）<br>・品目・消費量の取得と、買い物リストの組み立て<br>・品目名の重複の確認 |
| templates/ | ・各画面の HTML |
| public/static/style.css | ・買い物リスト画面（SCR-002）の見た目 |
| scripts/seed_demo.py | ・見本のデータを入れ直す（デモ用。実行前に接続先を表示し、確認を求める） |
| tests/ | ・calculations.py・validation.py の単体テスト |

#### 分け方の方針

- **機能ごとに分け、MVC のような層の分け方はしない**：画面6つ・テーブル3つの規模では、層ごとに分けると1つの機能を追うのに何か所も見る必要があり、かえって保守しにくいため。品目のことは routes/items.py を見れば分かる状態を優先する
- **計算と入力チェックは、画面とDBの処理から切り離す**：在庫入力と買い物リストで同じ計算を別々に書いていた時期に、片方だけ直して結果が食い違う不具合が実際に起きたため、1か所にまとめた。DB も Flask も使わないため、単体テストもしやすい
- **DB への接続は db.py の1か所にまとめる**：SQLite から PostgreSQL への移行では、接続まわりの変更が db.py だけで済んだ
- **ログインの確認は、各画面ではなく1か所で行う**：書き忘れた画面が無防備になるのを防ぐため。CSRF の確認より先に行う

### 5.4 External Integration and API Design（外部システム連携・API設計方針）

| Integration Target / API Name（連携先 / API名） | Method（連携方式） | Purpose / Overview（用途・概要） |
|---|---|---|
| Neon（PostgreSQL） | ・PostgreSQL の接続（直接接続）<br>・接続先は環境変数 `DATABASE_URL` で指定する | ・全データの保存と読み出し<br>・接続は10秒で諦める（下記） |
| GitHub → Vercel | ・GitHub のリポジトリを Vercel に取り込む<br>・Vercel が読み取れるのは restock-helper のリポジトリだけに限る | ・push すると自動で公開する。main は本番、ほかのブランチはプレビュー |

- 外部に公開する API は持たない（02 の 5.4）
- Vercel と Neon の連携機能は使わず、接続先は Vercel の環境変数に自分で設定する

#### DB への接続の待ち時間の上限（10秒）

- **きっかけ**：DB が応答しないとき、上限がないとエラーにならずに待ち続ける。ローカルで DB を止めて確かめたところ、メッセージが出るまで約5分かかった
- **10秒にした理由**：Neon の無料プランは5分使われないと休止し、この設定は変えられない。デモを見る人の最初の表示は、ほぼ毎回休止明けの接続になる。上限を短くしすぎると、休止明けの再開が遅れたときに、誤って「データを読み込めませんでした」が出るおそれがあるため、余裕を持たせる
- 上限は接続先1か所ごとにかかる。ローカルの `localhost` は2か所（IPv6 と IPv4）として扱われるため、ローカルで DB を止めた場合は約20〜30秒かかる

### 5.5 Scalability and Fault Tolerance（スケーラビリティ方針・障害対策）

| Aspect（観点） | Design Details（設計内容） |
|---|---|
| Scaling Policy（スケーリング方針） | 対象外。理由：1世帯・2人・数十件の規模で、増やす必要がないため |
| Redundancy（冗長化） | 対象外。理由：無料プランを使い、稼働の保証は求めないため（02 の 5.2） |
| Failover（フェイルオーバー） | 対象外。理由：同上 |
| Other Fault Tolerance（その他耐障害設計） | ・秘密の値が設定されていない、または DB が使えないときは、アプリを起動しない（不完全な状態で動かさない）<br>・DB への接続は10秒で諦め、利用者には決まったメッセージを出す（04 の 5.5）<br>・DB の処理は1回の操作ごとにまとめて確定し、途中で失敗したら取り消す（データを半端な状態で残さない） |

### 5.6 Infrastructure and Environment（インフラ・環境構成）

| Environment（環境） | Configuration / Resources（構成・リソース概要） |
|---|---|
| Development（開発） | ・Windows の PC で、Flask の開発用サーバーを動かす<br>・DB は PC の PostgreSQL 18（DB 名 `restock_helper`）<br>・秘密の値は `.env` に書き、Git には入れない |
| Staging（ステージング） | ・Vercel のプレビュー（ブランチを push すると作られる）<br>・Vercel にログインした本人しか開けない<br>・環境変数（DB の接続先・秘密の値）は本番と共通のため、本番と同じ DB を使う。プレビューで変えたデータは本番にも残る（扱いは 06） |
| Production（本番） | ・Vercel（Hobby プラン、シンガポール）＋ Neon（Free プラン、シンガポール）<br>・URL：https://restock-helper-theta.vercel.app<br>・環境変数は `DATABASE_URL`・`SECRET_KEY`・`APP_PASSWORD` の3つで、どれもローカルとは別の値<br>・ローカルとの違いは、ログイン状態の Cookie を HTTPS でしか送らない設定だけ（Vercel が自動で入れる環境変数で判定する） |

---

## 6. Open Issues（未決事項）

| ID | Open Issue（未決事項） | Owner（担当者） | Due Date（期限） | Status（ステータス） |
|---|---|---|---|---|
| TBD-001 | requirements.txt の pytest（開発中だけ使う）が、本番にもインストールされる。本番用と開発用でファイルを分けるか | SG-31 | 未確定 | Open |

---

## 7. Handoff to Detail Design（詳細設計への引き継ぎ）

- **計算と入力チェックは、DB も Flask も使わない形を保つ**：画面ごとに同じ処理を書かず、必ずここを使う
- **DB への接続は、必ず db.py を通す**：接続の上限や接続先の扱いを1か所で守るため
- **起動時の確認は、app.py の読み込み時に行う形を保つ**：Vercel では `python app.py` で起動しないため、`if __name__ == "__main__":` の中に移すと本番で確認が働かなくなる
