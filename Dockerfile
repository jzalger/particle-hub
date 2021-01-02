# sudo docker build -t particlehub:latest .
FROM python:3.8-alpine
RUN pip install pipenv
RUN mkdir -p /run/particlehub/
COPY particlehub /run/particlehub/
ADD Pipfile.lock /run/
ADD Pipfile /run/
ADD deploy/gunicorn_config.py /run/
ADD deploy/entrypoint.sh /run/
WORKDIR /run
RUN pipenv install --system --deploy --ignore-pipfile
EXPOSE 5000
ENTRYPOINT ["sh", "entrypoint.sh"]
