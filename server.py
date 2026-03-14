import json
import os
import re
import subprocess
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("PORT", "8000"))
API_KEY = os.environ.get("API_KEY", "")

INPUT_FORMATS = {
    "epub", "mobi", "azw3", "azw4", "docx", "odt", "txt", "rtf",
    "fb2", "html", "pdf", "lrf", "pdb",
}
OUTPUT_FORMATS = {"epub", "mobi", "docx", "lrf", "htmlz", "txt"}


def parse_multipart(content_type, body):
    """Parse multipart/form-data. Returns dict of {name: (filename|None, bytes)}."""
    match = re.search(r"boundary=(.+)", content_type)
    if not match:
        return {}
    boundary = match.group(1).strip().encode()

    fields = {}
    parts = body.split(b"--" + boundary)
    for part in parts:
        if part in (b"", b"--\r\n", b"--"):
            continue
        part = part.strip(b"\r\n")
        if b"\r\n\r\n" not in part:
            continue
        header_block, payload = part.split(b"\r\n\r\n", 1)
        headers_str = header_block.decode("utf-8", errors="replace")

        name_match = re.search(r'name="([^"]+)"', headers_str)
        if not name_match:
            continue
        name = name_match.group(1)

        filename_match = re.search(r'filename="([^"]*)"', headers_str)
        filename = filename_match.group(1) if filename_match else None

        fields[name] = (filename, payload)
    return fields


class ConvertHandler(BaseHTTPRequestHandler):
    def _check_auth(self):
        if not API_KEY:
            return True
        auth = self.headers.get("Authorization", "")
        if auth == f"Bearer {API_KEY}":
            return True
        self._json(401, {"error": "Invalid or missing API key"})
        return False

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok"})
            return

        if not self._check_auth():
            return

        if self.path == "/formats":
            self._json(200, {
                "input": sorted(INPUT_FORMATS),
                "output": sorted(OUTPUT_FORMATS),
            })
            return

        self.send_error(404)

    def do_POST(self):
        if not self._check_auth():
            return

        if self.path != "/convert":
            self.send_error(404)
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._json(400, {"error": "Expected multipart/form-data"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        fields = parse_multipart(content_type, body)

        if "file" not in fields or not fields["file"][0]:
            self._json(400, {"error": "Missing 'file' field"})
            return
        if "format" not in fields:
            self._json(400, {"error": "Missing 'format' field"})
            return

        filename = Path(fields["file"][0]).name
        file_data = fields["file"][1]
        output_format = fields["format"][1].decode().strip().lower()

        input_ext = Path(filename).suffix.lstrip(".").lower()
        if input_ext not in INPUT_FORMATS:
            self._json(400, {"error": f"Unsupported input format: {input_ext}"})
            return
        if output_format not in OUTPUT_FORMATS:
            self._json(400, {"error": f"Unsupported output format: {output_format}"})
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, filename)
            output_name = Path(filename).stem + "." + output_format
            output_path = os.path.join(tmpdir, output_name)

            with open(input_path, "wb") as f:
                f.write(file_data)

            result = subprocess.run(
                ["ebook-converter", input_path, output_path],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                stderr = result.stderr[-500:] if result.stderr else "unknown error"
                self._json(500, {"error": f"Conversion failed: {stderr}"})
                return

            with open(output_path, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{output_name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("", PORT), ConvertHandler)
    print(f"ebook-converter-api listening on port {PORT}")
    server.serve_forever()
