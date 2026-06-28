FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY tests ./tests
COPY scripts ./scripts
COPY startup.sh ./startup.sh
RUN chmod +x startup.sh && mkdir -p uploads
ENV PORT=8000
EXPOSE 8000
CMD ["./startup.sh"]
