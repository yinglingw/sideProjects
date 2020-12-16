#!/bin/bash -e

echo "Monitoring video dir..." > /tmp/se_test.txt

DIR="/var/www/html/media/"
inotifywait -m -r -e move -e create --format '%w%f' "$DIR" | while read f
sleep 5
do
  if [[ "$f" == *.mp4 ]]
  then
    echo Found a new video!
    sudo -H -u pi /usr/bin/python3 /home/pi/Scripts/twitter.py $DIR $f 2>&1 | tee -a /home/pi/Scripts/cameraTrapOutput.txt
  fi
done
