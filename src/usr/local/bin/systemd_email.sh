#!/bin/bash
adress="$NOTIFY_EMAIL"
nr_of_retries=10
until systemctl status $1 --full --lines=100 | iconv -c | \
    mail -s "`hostname`: service $1 failed" $adress || [ $((nr_of_retries--)) -eq 1 ]; do
  sleep 10
done

if [ $nr_of_retries -eq 0 ]; then
  echo "failed to send status to $adress"
  exit 1
else
  echo "status sent to $adress"
fi
