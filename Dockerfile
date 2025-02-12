FROM python:3.12-slim-bullseye

RUN mkdir /app

COPY * /app/

WORKDIR /app

# Install poetry
RUN pip install poetry

# Install dependencies using poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

EXPOSE 7860

CMD ["python3", "server.py"]