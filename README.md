# build_labels
use cn_CLIP to tag videos
Check the database every 2 minutes to see if there are any new videos, if there is a tag match, and then search; If not, wait 2 minutes

If you want to install the environment, use the following code：
```
pip install -r requirements.txt
```

If you want to start
```
python main.py
```

If you want to start and have a scheduled task, once an hour, type the following code into crontab on linux
```
crontab -e
0 * * * * sh build_labels/logs/get_start.sh >> build_labels/logs/cur_state.log 2>&1
```
Please change the above path to your folder path
This sh file includes a file lock. If the program in the previous time period has not finished running, the program in the current time period will continue to wait until the program in the previous time period has finished running
