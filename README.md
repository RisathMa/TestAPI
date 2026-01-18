# Clean Reader API

Production-ready FastAPI service for extracting clean, LLM-optimized Markdown from any web URL.

## Features

- **Mozilla Readability**: Extracts main article content, strips ads and navigation
- **Markdown Output**: Clean, structured Markdown optimized for LLMs
- **API Key Auth**: Bearer token authentication with usage tracking
- **Pay-per-use**: Transparent billing at $0.0015 per request
- **Metadata Extraction**: Title, author, publish date, and more

## Quick Start

### 1. Install Dependencies

```bash
cd "d:\Api Test"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Extract content (use demo key)
curl -X POST http://localhost:8000/v1/extract \
  -H "Authorization: Bearer sk_test_demo_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py              # Application entry point
├── config.py            # Configuration management
├── api/v1/
│   ├── extract.py       # POST /v1/extract endpoint
│   └── router.py        # API v1 router
├── db/
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # APIKey, UsageLog models
│   └── crud.py          # Database operations
├── middleware/
│   ├── auth.py          # API key authentication
│   ├── logging.py       # Request logging
│   └── usage.py         # Usage tracking
├── schemas/
│   ├── extract.py       # Request/response schemas
│   └── errors.py        # Error schemas
└── services/
    └── extractor.py     # Content extraction logic
```

## Pricing

| Feature | Price |
|---------|-------|
| Base request | $0.0015 |
| Large pages (>500KB) | +$0.001 |
| Image extraction | +$0.002 |
| Enterprise (>100K/month) | 30% off |

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Nginx deployment guide.
