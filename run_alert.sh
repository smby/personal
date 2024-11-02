#!/bin/bash

# Set the working directory
cd /home/smby1985/personal

# Add environment variables
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONPATH=/home/smby1985/personal

# Activate the virtual environment with full path
source /home/smby1985/personal/forum-alert-env/bin/activate

# Run the Python script with full path and proper error logging
python /home/smby1985/personal/snipe_hide_alert.py >> /home/smby1985/personal/cron_log.txt 2>&1

# Deactivate virtual environment
deactivate