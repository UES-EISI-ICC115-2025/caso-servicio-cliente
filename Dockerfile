# ---- Base image ----
FROM python:3.11-slim

# ---- Set working directory ----
WORKDIR /app

# ---- Install dependencies ----
COPY rag_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app ----
COPY rag_api/main.py .

# ---- Expose API port ----
EXPOSE 8001

# ---- Run server ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
