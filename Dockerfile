FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8000

WORKDIR /app

COPY paloalto/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY paloalto /app/paloalto

WORKDIR /app/paloalto

EXPOSE 8000

CMD ["python", "paloalto.py", "http"]
