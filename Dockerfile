FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

RUN mkdir -p /data
ENV DB_PATH=/data/multichkr.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "main.py"]
