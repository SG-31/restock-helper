"""
auto_git.py
-----------
git add / commit / push を対話形式で自動化する学習用スクリプト。

【設計方針】
- subprocess.run() には「リスト形式」で引数を渡す（shell=True は使わない）。
  文字列を組み立てて shell=True で実行すると、コマンドインジェクション
  （悪意ある文字列が紛れ込んで想定外のコマンドが実行される）のリスクがある。
  リスト形式なら、各要素がそのまま1つの引数として扱われるため安全。
- git add -A（全部まとめて追加）ではなく、変更されたファイルを一覧表示してから
  ユーザーに確認を取る。理由：意図せず.envや秘密情報を含むファイルを
  一緒にコミットしてしまう事故を防ぐため。
- push は毎回自動実行せず、必ず確認を挟む（普段の「commitは都度、pushはまとめて」
  という運用にも合わせやすい）。
"""

import subprocess
import sys


def run_git(args):
    """git コマンドを実行し、標準出力を返す。エラー時は例外を投げる。"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print("エラーが発生しました:")
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def show_status():
    """現在の変更状況を表示する。"""
    status = run_git(["status", "--porcelain"])
    if not status.strip():
        print("変更はありません。コミットするものがないので終了します。")
        sys.exit(0)
    print("--- 現在の変更 ---")
    print(status)
    return status


def confirm(question):
    """y/n で確認を取る。yes以外は全てNoとして扱う。"""
    answer = input(f"{question} (y/n): ").strip().lower()
    return answer == "y"


def main():
    show_status()

    if not confirm("これらの変更を git add してよいですか？"):
        print("中断しました。")
        return

    # git add -A ではなく、変更のあった範囲だけを追加する
    run_git(["add", "."])
    print("git add が完了しました。")

    message = input("コミットメッセージを入力してください: ").strip()
    if not message:
        print("コミットメッセージが空です。中断しました。")
        return

    run_git(["commit", "-m", message])
    print(f"コミットしました: {message}")

    if confirm("続けて git push しますか？"):
        run_git(["push"])
        print("push が完了しました。")
    else:
        print("push は行いませんでした（後でまとめて実行できます）。")


if __name__ == "__main__":
    main()
