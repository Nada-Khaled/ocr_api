# OCR API

A FastAPI service that wraps the AI OCR code (EasyOCR, Arabic + English) and serves it over HTTP, containerized with Docker.

## Project structure

```
app/
  main.py   # FastAPI app and routes
  ocr.py    # EasyOCR loading and text extraction
Dockerfile
requirements.txt
```

## Run locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run with Docker

Build the image:

```bash
docker build -t ocr-api .
```

Run the container:

```bash
docker run -p 8000:8000 ocr-api
```

## Usage

- `GET /health` — health check
- `POST /ocr` — upload an image file (`multipart/form-data`, field name `file`), returns extracted text as JSON

Example:

```bash
curl -X POST http://localhost:8000/ocr -F "file=@image.png"
```

Response:

```json
{
  "filename": "image.png",
  "text": "extracted text here"
}
```

## API docs

Once running, interactive API docs are available at `http://localhost:8000/docs`.
