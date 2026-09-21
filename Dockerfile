FROM python:3.14-slim
WORKDIR /chat
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY poetry.lock .
COPY pyproject.toml .
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --without dev
COPY . .
CMD ["python", "-m", "app.main", "-m", "prod"]
