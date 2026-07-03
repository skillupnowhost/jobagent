FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ .
COPY --from=frontend-build /frontend/dist ./static

RUN mkdir -p resumes

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 1 --bind 0.0.0.0:8000 --timeout 120"]
