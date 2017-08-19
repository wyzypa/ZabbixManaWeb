#/bin/bash
start() {
#    pidfile='/opt/zabbix/tmp/zabbix_agentd.pid'
##    if [ ! -f ${pidfile} ];then
##        echo "Pidfile Not Found"
#        exit 1
#    fi
#    pid=$(cat ${pidfile})

    if [[ `ps -ef | grep "zabbix_agentd" | grep -v 'grep' | wc -l` -ne 0 ]];then
        echo 'Zabbix Is Already Running!'
        exit 1
    else
        /opt/zabbix/sbin/zabbix_agentd -c /opt/zabbix/conf/zabbix_agent.conf 
        if [ $? -eq 0 ];then
            echo 'Zabbix Start Successed!' 
        fi
    fi
}
stop(){
    if [[ `ps -ef | grep "zabbix_agentd" | grep -v 'grep' | wc -l` -eq 0 ]];then
        echo "zabbix_agentd Not Running"
        exit 1
    else
        killall zabbix_agentd
        if [ $? -eq 0 ];then
            echo 'Zabbix Stop Successed!' 
        fi
    fi
}
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 3s
        start
        ;;
    *)
        echo "use zabbix.sh {start | stop | restart}"
esac
