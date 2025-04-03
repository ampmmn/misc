# code:utf-8
import time
import os
import re
from datetime import datetime

TODOTXT_PATH="todo.txt"
DONETXT_PATH="done.txt"

last_mod_time = None

current_task_name = ""
task_info = []

def is_task_changed(task_name):
    if len(task_info) == 0:
        return True
    entry = task_info[-1]
    return task_name == entry["task_name"]

def update_task_info(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 完了済はスキップ
            if re.match(r'^x ', line) != None:
                continue

            # 扱わない記法をカット
            line = re.sub(r' +due:\d\d\d\d-\d\d-\d\d', '', line)
            line = re.sub(r'^(\([A-Z]\) )?(\d\d\d\d-\d\d-\d\d )?', '', line)

            task_name = line

            # 変化したら登録
            if is_task_changed(task_name):

                now = datetime.now()

                if len(task_info) > 0:
                    old_entry = task_info[-1]
                    old_entry["end"] = now

                entry = { "task_name":task_name, "start":now, "end":None }
                task_info.append(entry)

                current_task_name = line
                return


def watch_todotxt(file_path):

    if os.path.exists(file_path) == False:
        print("not found")
        return

    # 更新日時
    mod_time = os.path.getmtime(file_path)

    global last_mod_time

    if mod_time == last_mod_time:
        print("same")
        return

    print("updated")
    last_mod_time = mod_time 
    update_task_info(file_path)

def main():
    while True:
        watch_todotxt(TODOTXT_PATH)

        # ToDo: ファイル監視とは別に一定間隔でレポート生成

        time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

