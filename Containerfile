FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    fonts-liberation \
    libxml2-dev \
    libxslt-dev \
    pkg-config \
    zlib1g-dev \
    build-essential \
    git \
  && pip install --no-cache-dir cython \
  && pip install --no-cache-dir --no-binary lxml lxml \
  && pip install --no-cache-dir --no-binary html5-parser \
    git+https://github.com/gryf/ebook-converter.git \
  && pip install --no-cache-dir "setuptools<71" \
  && apt-get purge -y build-essential git \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server.py .

EXPOSE 8000

CMD ["python", "server.py"]
