@echo off
docker exec spark-master /opt/spark/bin/spark-submit --master local[*] --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0 /opt/spark/work-dir/src/consumers/consumer.py
pause