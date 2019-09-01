#!/bin/bash

cd /home/xuejun/lib_data/
cnt=0
while true
do
	cnt=`expr $cnt + 1`
	status=$?
	python3 ip_proxy.py
	if [ $status == 0 ]
	then
		echo "find correct proxy ip!"
		python3 main.py
		status1=$?
		if [ $status1 == 20 ]
		then
			echo "can't get token!"
			continue
		elif [ $status1 == 30 ]
		then
			echo "lost too many seats!"
			continue
		else
			echo "unknown error for main.py!"
			break
		fi
	elif [ $status == 10 ]
	then
		echo "can't find effective proxy ip!"
		if [$cnt < 5]
		then
			continue
		else
			echo "try five times, they all failed!"
			break
		fi
	else
		echo "unknown error for proxy.py!"
		break
	fi
done

