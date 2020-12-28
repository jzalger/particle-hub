#!/bin/bash
exec pipenv run gunicorn --config /particlehub/gunicorn_config.py particlehub.wsgi:particlehub
