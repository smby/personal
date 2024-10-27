#!/bin/bash
# Activate the virtual environment
source /home/smby1985/forum-alert-env/bin/activate
# Run the Python script
python /home/smby1985/snipe_hide_alert.py >> /home/smby1985/log.txt 2>&1