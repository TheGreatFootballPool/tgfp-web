FROM python:3.10

RUN mkdir /app
WORKDIR /app

COPY pyproject.toml /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY flask_site /app

CMD ["gunicorn", "-b", "0.0.0.0:80",  "app:app"]