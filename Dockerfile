# sudo docker build -t particlehub:latest .
FROM python:3.8-alpine
RUN pip install pipenv
RUN mkdir -p /deploy/particlehub/
COPY particlehub /deploy/particlehub/
ADD Pipfile.lock /deploy/
ADD Pipfile /deploy/
ADD entrypoint.sh /deploy/
WORKDIR /deploy
RUN pipenv install --system --deploy --ignore-pipfile
EXPOSE 5000
ENTRYPOINT ["sh", "entrypoint.sh"]
