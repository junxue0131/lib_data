ps aux|grep run.sh|grep -v grep|cut -c 9-15|xargs kill -15
echo "run.sh is killed!"

ps aux|grep main.py|grep -v grep|cut -c 9-15|xargs kill -15
ps aux|grep ip_proxy.py|grep -v grep|cut -c 9-15|xargs kill -15
echo "python script is killed!"