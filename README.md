# Restock Helper

| Item（項目） | Value（値） |
|---|---|
| Document ID（文書ID） | RH-README |
| Version（バージョン） | 0.1 |
| Status（ステータス） | Draft |
| Created Date（作成日） | 2026-10-14 |
| Last Updated（最終更新日） | 2026-10-14 |
| Owner（管理者） | SG-31 |
| Related Documents（関連文書） | [docs/01_REQUEST_DEFINITION.md](docs/01_REQUEST_DEFINITION.md) 〜 06（作成中） |

> **現在の状態**：アプリは公開済みです。設計書は作成中です。

---

## Table of Contents（目次）

1. [Project Overview（プロジェクト・機能の概要）](#1-project-overviewプロジェクト機能の概要)
2. [Problem / Solution / Benefit Summary（問題・解決・効果の概要）](#2-problem--solution--benefit-summary問題解決効果の概要)
3. [Screen Overview（画面概要）](#3-screen-overview画面概要)
4. [Design Documents Index（設計書一覧）](#4-design-documents-index設計書一覧)
5. [Overall Design Policy（設計上の全体方針・前提）](#5-overall-design-policy設計上の全体方針前提)
6. [Glossary（用語集・略語定義）](#6-glossary用語集略語定義)
7. [Document Owners and Reviewers（文書管理者・レビュアー一覧）](#7-document-owners-and-reviewers文書管理者レビュアー一覧)
8. [Demo and Getting Started（デモ・動かし方）](#8-demo-and-getting-starteddemo動かし方)

---

## 1. Project Overview（プロジェクト・機能の概要）

ひとり暮らしの高齢者の日用品を、**買い忘れず・買いすぎず**に補充するための買い物リストアプリです。
ヘルパーが週1回在庫数を入力すると、消費のペースから補充する数を計算し、買い物リストを作ります。

---

## 2. Problem / Solution / Benefit Summary（問題・解決・効果の概要）

| Item（項目） | Summary（概要） | Detail Document（詳細文書） |
|---|---|---|
| Current Problems（現在の問題点） | ひとり暮らしの高齢者は、在庫の把握が難しくなり、日用品の不足や重複買いが起きる。支援者に適量を伝えることも難しい | [01](docs/01_REQUEST_DEFINITION.md) |
| Development Purpose（開発目的） | 身内の困りごとを解決するため、役割を「必需品の適切な補充」に絞って在庫管理を支える | [01](docs/01_REQUEST_DEFINITION.md) |
| Solution Approach（解決方針） | 週1回の在庫入力から消費のペースを求め、次の買い出しまでに必要な数を出す | [01](docs/01_REQUEST_DEFINITION.md) |
| System Functions（システム機能） | 在庫入力と補充数の計算、買い物共有画面（買い物リストと「買ってほしいもの」）、買い物完了、管理品目の編集、ログイン | [02](docs/02_REQUIREMENTS_DEFINITION.md) |
| Expected Benefits（期待効果） | 欠品と買いすぎが減り、高齢者もリストを見て必要な物を頼める | [01](docs/01_REQUEST_DEFINITION.md) |
| Completion Criteria（完成判定基準） | 在庫入力で補充する数が出る／高齢者がリストを見て依頼できる／買い物完了が在庫に反映される | [01](docs/01_REQUEST_DEFINITION.md) |

---

## 3. Screen Overview（画面概要）

画面の画像は準備中です。

主な画面：トップ、買い物リスト（高齢者用）、在庫入力（ヘルパー用）、管理品目、ログイン

---

## 4. Design Documents Index（設計書一覧）

| File（ファイル名） | Document Name（文書名） | Status（ステータス） | Version（バージョン） | Owner（担当者） |
|---|---|---|---|---|
| [01_REQUEST_DEFINITION.md](docs/01_REQUEST_DEFINITION.md) | Request Definition（要求定義） | Draft | 0.1 | SG-31 |
| [02_REQUIREMENTS_DEFINITION.md](docs/02_REQUIREMENTS_DEFINITION.md) | Requirements Definition（要件定義） | Draft | 0.1 | SG-31 |
| 03_DATA_AND_SECURITY_DESIGN.md | Data and Security Design（データ・セキュリティ設計） | 作成中 | - | SG-31 |
| 04_UI_AND_FLOW_DESIGN.md | UI and Flow Design（UI・フロー設計） | 作成中 | - | SG-31 |
| 05_ARCHITECTURE_DESIGN.md | Architecture Design（アーキテクチャ設計） | 作成中 | - | SG-31 |
| 06_OPERATION_AND_HANDOFF.md | Operation and Handoff Design（運用・詳細設計引き継ぎ） | 作成中 | - | SG-31 |

---

## 5. Overall Design Policy（設計上の全体方針・前提）

- 現在の仕様は、上記の設計書（01〜06）を正本とする
- 開発中の検討の経緯と判断の理由は [docs/archive/decisions_v7.1.md](docs/archive/decisions_v7.1.md) に残している（2026-10-14 に凍結）
- 公開版はデモ用で、見本のデータだけを入れる。実在の世帯のデータは扱わない
- 1世帯専用の設計とする。複数の世帯で使う場合は、世帯ごとに別に公開する

---

## 6. Glossary（用語集・略語定義）

| Term / Abbreviation（用語・略語） | Definition（定義） |
|---|---|
| 管理品目 | 在庫の数を記録して、補充する数を計算する日用品 |
| 買ってほしいもの | 高齢者が自由な文で追加する、管理品目以外の依頼（買い物完了で消える） |
| 消費量 | 前回の在庫数と今回の在庫数の差（増えていた場合は0） |
| 適正在庫数 | 直近4回の消費量の平均 × 1.5 |
| 補充する数 | 適正在庫数 − 今の在庫数（端数は切り上げ、マイナスなら0） |
| 買い物完了 | 補充する数を在庫数に足し、「買ってほしいもの」を消す操作 |

---

## 7. Document Owners and Reviewers（文書管理者・レビュアー一覧）

| Role（役割） | Name（氏名） | Assigned Documents（担当文書） |
|---|---|---|
| Document Owner（文書管理者） | SG-31 | All Documents（全文書） |
| Reviewer（レビュアー） |  |  |

---

## 8. Demo and Getting Started（デモ・動かし方）

### デモ

- URL：https://restock-helper-theta.vercel.app
- パスワード：応募書類に記載しています
- 中身は見本のデータです。見本データは不定期に初期化します

### 技術構成

Python 3.13、Flask、PostgreSQL（Neon）、Vercel。詳細は 05（作成中）

### ローカルでの動かし方

前提：Python 3.13 と PostgreSQL

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # DATABASE_URL・SECRET_KEY・APP_PASSWORD を設定する
python app.py
```

テスト：`python -m pytest`
