FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ca-certificates curl jq iputils-ping

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ .

CMD ["python", "main.py"]