FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Only runtime assets: credentials and .env cannot enter this image.
COPY app ./app
COPY data ./data
COPY models ./models
ENV PORT=8080
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 90 app.server:app"]
