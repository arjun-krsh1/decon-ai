# Decon AI — Streamlit on a Hugging Face Docker Space.
# Pinned Python 3.12 + requirements.txt = a byte-for-byte clone of local.
FROM python:3.12-slim

WORKDIR /app

# Install deps first (layer-cached); all pins ship manylinux wheels — no compiler needed.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App code (the HF Space repo contains only tracked files — no venv/.env/caches).
COPY . .

# Streamlit config via env so no interactive prompts; HOME writable for its config/cache.
ENV HOME=/app \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
