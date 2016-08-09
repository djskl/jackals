from __future__ import absolute_import

from celery import Celery

app = Celery(
    main='tasks',
    config_source="settings",
    include="tasks"
)