#!/bin/bash
adress="$NOTIFY_EMAIL"
subject="`hostname` has restarted"
echo "Sending reboot notification to $adress"
nr_of_retries=10
until journalctl --since="-15 minutes" | mail -s "$subject" $adress || [ $((nr_of_retries--)) -eq 1 ]; do
  sleep 10
done

if [ $nr_of_retries -eq 0 ]; then
  echo "failed to send reboot notification"
  exit 1
else
  echo "reboot notification sent to $adress"
fi
