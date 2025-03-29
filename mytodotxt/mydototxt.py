# code:utf-8
import os
import subprocess
import time
import argparse
import sys
import re
from datetime import datetime

TODOTXT_PATH="todo.txt"
DONETXT_PATH="done.txt"

# ファイルがなければ新規作成
def create_todotxt_if_not_exist():
    if os.path.exists(TODOTXT_PATH):
        return

    f = open(TODOTXT_PATH, "w")
    f.close()

# タスクを列挙
def do_ls(args):

    create_todotxt_if_not_exist()

    with open(TODOTXT_PATH, "r", encoding="utf-8") as f:
        for index, line in enumerate(f, start=1):
            line = line.strip()
            print(f"{index} {line}")

def load_tasks(file_path):
    tasks = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            tasks.append(line.strip())
    return tasks

def save_tasks(tasks, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for line in tasks:
            f.write(f"{line}\n")

def save_append_tasks(tasks, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        for line in tasks:
            f.write(f"{line}\n")

# タスクをついか
def do_add(args):

    create_todotxt_if_not_exist()

    with open(TODOTXT_PATH, "a", encoding="utf-8") as f:
        f.write(f"{args.content}\n")

# タスクを削除
def do_rm(args):

    create_todotxt_if_not_exist()

    tasks = load_tasks(TODOTXT_PATH)

    sorted_no = args.no
    sorted_no.sort(reverse=True)
    for no in sorted_no:
        if no < 1 or len(tasks) < no:
            sys.stderr.write(f"{no}行はない") 
            continue

        del tasks[no-1]

    save_tasks(tasks, TODOTXT_PATH)

def do_pend(no, content, is_append):

    tasks = load_tasks(TODOTXT_PATH)

    if no < 1 or len(tasks) < no:
        sys.stderr.write(f"{no}行はない") 
        return False

    line = tasks[no-1]
    tasks[no-1] = f"{line} {content}" if is_append else f"{content} {line}"

    save_tasks(tasks, TODOTXT_PATH)
    return True

# タスクを既存行に追加(末尾)
def do_append(args):
    create_todotxt_if_not_exist()
    do_pend(args.no, args.content, True)
    
# タスクを既存行に追加(先頭)
def do_prepend(args):
    create_todotxt_if_not_exist()
    do_pend(args.no, args.content, False)

# タスク着手
def do_start(args):
    create_todotxt_if_not_exist()
    tasks = load_tasks(TODOTXT_PATH)

    no = args.no
    if no < 1 or len(tasks) < no:
        sys.stderr.write(f"{no}行はない") 
        return

    hhmm = datetime.now().strftime("%H:%M")

    line = tasks[no-1]
    line = re.sub(r' *start:\d\d:\d\d', '', line)
    tasks[no-1] = f"{line} start:{hhmm}"
    save_tasks(tasks, TODOTXT_PATH)

# タスク完了
def do_do(args):
    create_todotxt_if_not_exist()
    tasks = load_tasks(TODOTXT_PATH)

    no = args.no
    if no < 1 or len(tasks) < no:
        sys.stderr.write(f"{no}行はない") 
        return

    line = tasks[no-1]
    if re.match(r'^x .*', line) != None:
        sys.stderr.write(f"{no}行はすでに終わっている") 
        return

    hhmm = datetime.now().strftime("%H:%M")

    tasks[no-1] = f"x {line} end:{hhmm}"
    save_tasks(tasks, TODOTXT_PATH)

# タスクに優先度を付与する
def set_priority(no, priority):
    create_todotxt_if_not_exist()

    if priority != '':
        if re.match(r'[A-Z]', priority) == None:
            sys.stderr.write(f"優先度はA-Zで指定する必要がある") 
            return False

    tasks = load_tasks(TODOTXT_PATH)

    no = args.no
    if no < 1 or len(tasks) < no:
        sys.stderr.write(f"{no}行はない") 
        return False

    if re.match(r'^x .*', tasks[no-1]) != None:
        sys.stderr.write(f"{no}行はすでに終わっている") 
        return False

    # 既存の優先度をカット
    line = re.sub(r' *\([A-Z]\) (.+)$', r'\1', tasks[no-1])

    # 優先度を付与する
    if priority != '':
        tasks[no-1] = f"({priority}) {line}"

    save_tasks(tasks, TODOTXT_PATH)
    return True

# タスクに優先度を付与する
def do_pri(args):
    set_priority(args.no, args.priority)

# タスクから優先度をはずず
def do_depri(args):
    set_priority(args.no, '')

# 完了したタスクをdone.txtに移動する
def do_clean(args):
    comp_tasks = []
    uncomp_tasks = []

    tasks = load_tasks(TODOTXT_PATH)
    for line in tasks:
        if re.match(r'^x.+$', line) != None:
            comp_tasks.append(line)
        else:
            uncomp_tasks.append(line)

    save_tasks(uncomp_tasks, TODOTXT_PATH)
    save_append_tasks(comp_tasks, DONETXT_PATH)

def main():

    parser = argparse.ArgumentParser(description="自分用ToDo.txtクライアント")

    sub_parsers = parser.add_subparsers(dest="command", help="コマンド")

    # 列挙コマンド
    cmd_ls = sub_parsers.add_parser("ls", help="タスクを列挙する")
    cmd_ls.set_defaults(handler=do_ls)

    cmd_add = sub_parsers.add_parser("add", help="新しいタスクを追加する")
    cmd_add.add_argument("content", type=str, help="タスクの内容")
    cmd_add.set_defaults(handler=do_add)

    cmd_app = sub_parsers.add_parser("append", help="既存のタスクに情報を追加(末尾)する")
    cmd_app.add_argument("no", type=int, help="タスク行番号")
    cmd_app.add_argument("content", type=str, help="追加したい内容")
    cmd_app.set_defaults(handler=do_append)
    
    cmd_prep = sub_parsers.add_parser("prepend", help="既存のタスクに情報を追加(先頭)する")
    cmd_prep.add_argument("no", type=int, help="タスク行番号")
    cmd_prep.add_argument("content", type=str, help="追加したい内容")
    cmd_prep.set_defaults(handler=do_prepend)

    cmd_start = sub_parsers.add_parser("start", help="タスクに着手する")
    cmd_start.add_argument("no", type=int, help="タスク行番号")
    cmd_start.set_defaults(handler=do_start)

    cmd_do = sub_parsers.add_parser("do", help="タスクを完了にする")
    cmd_do.add_argument("no", type=int, help="タスク行番号")
    cmd_do.set_defaults(handler=do_do)

    cmd_rm = sub_parsers.add_parser("rm", help="タスクを削除")
    cmd_rm.add_argument("no", type=int, nargs="+", help="タスク行番号")
    cmd_rm.set_defaults(handler=do_rm)

    cmd_pri = sub_parsers.add_parser("pri", help="タスクに優先度を付与")
    cmd_pri.add_argument("no", type=int, help="タスク行番号")
    cmd_pri.add_argument("priority", type=str, help="優先度(A-Z)")
    cmd_pri.set_defaults(handler=do_pri)

    cmd_depri = sub_parsers.add_parser("depri", help="タスクから優先度を外す")
    cmd_depri.add_argument("no", type=int, help="タスク行番号")
    cmd_depri.set_defaults(handler=do_depri)

    cmd_clean = sub_parsers.add_parser("clean", help="完了したタスクをdone.txtに移動")
    cmd_clean.set_defaults(handler=do_clean)

    args, unknown = parser.parse_known_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

