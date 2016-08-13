from celery_server.app import script_worker

script_worker.delay("123", "/root/git/uwsgi-websocket/celery_server/ces.py")

