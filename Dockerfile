FROM python:3.12-alpine

ENV PATH="/root/.local/bin:$PATH" POETRY_VIRTUALENVS_CREATE=false

RUN apk add --no-cache curl

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY . .

RUN chown -R guest:users /app

USER guest