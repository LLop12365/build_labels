#!/bin/bash

LOCK_FILE="/home/program/build_labels/logs/cur.lock"
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p $PID > /dev/null; then
        echo "程序正在运行中 PID $PID. 正在等待..."
        while ps -p $PID > /dev/null; do
            sleep 3
        done
        echo "程序 PID $PID 运行完成. Proceeding..."
    else
        echo "Lock file存在，但是程序没有运行，移除lock file并开始执行文件."
        rm "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
printf "\n\n"
source /etc/profile
date

source /root/anaconda3/bin/activate labels
python /home/program/build_labels/version/v1h.py
rm "$LOCK_FILE"
