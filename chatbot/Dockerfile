# Builds the chatbot service for Railway (or any Docker host). Set the service's root directory to /chatbot.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Run as a normal user. The embedding model is cached under this user's home, so the build step that
# downloads it and the running server must be the SAME user, or it would be downloaded again at runtime.
RUN useradd --create-home --uid 1000 app
WORKDIR /app
RUN chown app:app /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app src ./src
COPY --chown=app:app data ./data

USER app

# Build the vector index now (this also downloads the ~80 MB embedding model), so every container starts ready.
# Changing the CV means rebuilding the image, which is the point: the database is part of the release.
RUN python src/indexing.py --index

# Railway injects $PORT. A Dockerfile start command runs in exec form, which does not expand variables,
# hence the shell wrapper (see Railway's "Set a Start Command" docs).
CMD ["sh", "-c", "exec uvicorn api:app --app-dir src --host 0.0.0.0 --port ${PORT:-8000}"]
