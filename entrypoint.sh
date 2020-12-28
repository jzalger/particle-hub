#!/bin/bash
exec pipenv run gunicorn --config gunicorn_config.py particlehub.wsgi:particlehub
