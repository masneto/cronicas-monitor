FROM python:3.11-slim

WORKDIR /app
COPY . .

# Instala certificados CA e utilitários úteis
RUN apt-get update && apt-get install -y ca-certificates curl jq iputils-ping

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]