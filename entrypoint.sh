#!/bin/bash
pwd
ls -ls
exec pipenv run gunicorn --config particlehub/gunicorn_config.py particlehub.wsgi:particlehub_app
