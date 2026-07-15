FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --index-url "$PIP_INDEX_URL" --no-cache-dir -r requirements.txt

COPY real_llm_client.py cost_runtime.py ./
COPY tests ./tests

CMD ["python", "-m", "pytest", "-q"]
