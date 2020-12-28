FROM python:3.8-slim
RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile
RUN pipenv shell
RUN mkdir /deploy
WORKDIR /deploy
EXPOSE 5000
ENTRYPOINT ["sh", "entrypoint.sh"]
