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
curl -F file=@book.epub -F format=mobi http://localhost:8000/convert -o book.mobi
```

### `GET /formats`

List supported input and output formats.

### `GET /health`

Health check. Returns `{"status": "ok"}`.

## Running

```bash
podman build -t ebook-converter-api .
podman run -d -p 8000:8000 ebook-converter-api
```
