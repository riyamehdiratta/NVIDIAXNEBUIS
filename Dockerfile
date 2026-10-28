FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 THREADLINE_DATA_DIR=/var/lib/threadline THREADLINE_IMPORT_DIR=/var/lib/threadline/imports
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/app /app/backend/app
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist
RUN mkdir -p /var/lib/threadline/imports && useradd --create-home --uid 10001 threadline && chown -R threadline:threadline /var/lib/threadline
USER threadline
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
