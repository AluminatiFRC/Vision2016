#! /bin/sh

#Configure camera
v4l2-ctl -d /dev/video0 -c exposure_auto=1 -c exposure_absolute=5

#Start script
python /home/pi/Vision2016/vision.py --release &
