基于celery&websocket实现，celery负责执行python脚本，websocket负责在前端实时展示脚本日志，消息传递使用Redis

## features
1 浏览器**实时**展示日至
2 任务状态(`排队`、`运行`、`失败`、`停止`，`成功`)监控
3 结点状态(`上线`、`掉线`)监控

## 安装依赖
```
pip install -r docs/requirements.txt
```

## 使用

1 - 启动celery服务
```
cd celery_server
celery worker -A app -l info
python worker.py  #监视任务状态
```
2 - 启动uwsgi
```
uwsgi --ini uws.ini
```


