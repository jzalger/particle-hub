FROM python:3.8-alpine
RUN pip install pipenv
RUN mkdir -p /run/particlehub/
COPY particlehub /run/particlehub/
ADD Pipfile.lock /run/
ADD Pipfile /run/
COPY deploy /run/
WORKDIR /run
RUN pipenv install --system --deploy --ignore-pipfile
EXPOSE 5000
ENTRYPOINT ["sh", "entrypoint.sh"]
