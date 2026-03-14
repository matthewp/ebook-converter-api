# ebook-converter-api

A minimal HTTP API for ebook format conversion, powered by [gryf/ebook-converter](https://github.com/gryf/ebook-converter).

## API

### `POST /convert`

Convert an ebook file to a different format.

**Request:** `multipart/form-data` with:
- `file` — the ebook file
- `format` — target format (epub, mobi, docx, lrf, htmlz, txt)

**Response:** the converted file as `application/octet-stream`

```bash
curl -H "Authorization: Bearer YOUR_KEY" \
  -F file=@book.epub -F format=mobi \
  http://localhost:8000/convert -o book.mobi
```

### `GET /formats`

List supported input and output formats.

### `GET /health`

Health check. Returns `{"status": "ok"}`.

## Authentication

Set the `API_KEY` environment variable to require a Bearer token on all endpoints (except `/health`). If unset, no authentication is required.

## Running

Pre-built images are available from GitHub Container Registry:

```bash
podman pull ghcr.io/matthewp/ebook-converter-api:latest
podman run -d -p 8000:8000 -e API_KEY=your-secret ghcr.io/matthewp/ebook-converter-api:latest
```

To build from source:

```bash
podman build -t ebook-converter-api .
podman run -d -p 8000:8000 -e API_KEY=your-secret ebook-converter-api
```
