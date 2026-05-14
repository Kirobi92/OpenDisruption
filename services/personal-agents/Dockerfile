FROM python:3.11-slim

WORKDIR /app

COPY services/personal-agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/personal-agents/app/ ./app/

# Profile werden als Volume gemountet (FAMILY_PRIVATE — nicht im Image!)
VOLUME ["/app/profiles"]

EXPOSE 8017

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8017"]
