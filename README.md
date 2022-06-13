#### 启动脚本

```
后台启动 服务
nohup python3 /root/vpn_cms/manage.py runserver 0.0.0.0:8000  > /root/vpn_cms_log.txt 2>&1 &
```

```
# 生成静态文件
python3 /root/vpn_node_cms/manage.py collectstatic

# 启动
/usr/local/python3/bin/uwsgi --ini /root/vpn_cms/uwsgi.ini  
# 停止
/usr/local/python3/bin/uwsgi --stop /root/vpn_cms/uwsgi.pid
# 重启
/usr/local/python3/bin/uwsgi --reload /root/vpn_cms/uwsgi.pid
```


```
nohup python3 /root/vpn_cms/start_script/check_user_flow.py  > /root/check_user_flow_log.txt 2>&1 &
# 更新trojan节点
nohup python3 /root/vpn_cms/start_script/get_node.py  > /root/get_node.txt 2>&1 &
# 更新ssr 节点
nohup python3 /root/vpn_cms/start_script/get_nodes_ssr.py  > /root/vpn_cms_log.txt 2>&1 &

# 用户留存统计
nohup python3 /root/vpn_cms/start_script/data_statistics.py  > /root/log/data_statistics.txt 2>&1 &

# 检测用户状态
nohup python3 /root/vpn_cms/start_script/check_user_status.py  > /root/log/check_user_status.txt 2>&1 &

# 线路统计
nohup python3 /root/vpn_cms/start_script/analytic_statistics.py  > /root/log/analytic_statistics.txt 2>&1 &
nohup python3 /root/vpn_cms/start_script/check_statistics.py  > /root/log/check_statistics.txt 2>&1 &

上报节点状态
nohup python3 /root/vpn_cms/start_script/query_node_status.py  > /root/log/query_node_status.txt 2>&1 &

 删除用户
nohup python3 /root/vpn_cms/start_script/del_temp_user.py  > /root/log/del_temp_user.txt 2>&1 &

 上报ping和连接数据
nohup python3 /root/vpn_cms/start_script/report_update.py  > /root/log/report_update.txt 2>&1 &

```



