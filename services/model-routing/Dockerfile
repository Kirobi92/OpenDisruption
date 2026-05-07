FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic
COPY main.py .
EXPOSE 8009
CMD ["python", "main.py"]
