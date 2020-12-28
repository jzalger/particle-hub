FROM python:3.8-alpine
RUN pip install pipenv
RUN mkdir /particlehub
COPY particlehub/* /particlehub/
ADD Pipfile.lock /particlehub/
ADD Pipfile /particlehub/
ADD entrypoint.sh /particlehub/
WORKDIR /particlehub
RUN ls -la
RUN pipenv install --system --deploy --ignore-pipfile
EXPOSE 5000
ENTRYPOINT ["sh", "entrypoint.sh"]
