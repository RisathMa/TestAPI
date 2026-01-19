# Clean Reader API

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)

> **LLM-Ready Content Extraction** — Convert any URL to clean Markdown in one API call.

Production-ready FastAPI service for extracting clean, LLM-optimized Markdown from any web URL. Perfect for RAG pipelines, content aggregation, and AI applications.

## ✨ Features

- **Mozilla Readability**: Extracts main article content, strips ads and navigation
- **Markdown Output**: Clean, structured Markdown optimized for LLMs
- **Tiered Rate Limiting**: Per-minute and per-day limits based on your tier
- **Usage Tracking**: Real-time usage stats and billing dashboard
- **Pay-per-use**: Transparent billing starting at $0.0015 per request
- **Metadata Extraction**: Title, author, publish date, and more

## 💰 Pricing

| Tier | Monthly Requests | Rate Limit | Price |
|------|------------------|------------|-------|
| **Free** | 100 | 10/min | $0 |
| **Developer** | 5,000 | 60/min | $7.50/mo |
| **Pro** | 25,000 | 300/min | $30/mo |
| **Business** | 100,000 | 1000/min | $100/mo |
| **Enterprise** | Unlimited | Custom | Contact us |

### Pay-Per-Use Add-ons
| Feature | Cost |
|---------|------|
| Base request (≤500KB) | $0.0015 |
| Large pages (>500KB) | +$0.001 |
| Image extraction | +$0.002 |
| PDF extraction | +$0.003 |

**Tier Discounts**: Pro (10% off), Business (30% off), Enterprise (40% off)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
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
curl https://api.companyrm.lk/health

# Extract content (use demo key)
curl -X POST https://api.companyrm.lk/v1/extract \
  -H "Authorization: Bearer sk_test_demo_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check your account status
curl https://api.companyrm.lk/v1/account \
  -H "Authorization: Bearer sk_test_demo_key"

# View usage statistics
curl https://api.companyrm.lk/v1/usage \
  -H "Authorization: Bearer sk_test_demo_key"
```

## 📚 API Endpoints

### Content Extraction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/extract` | Extract content from URL |

### Account & Usage
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/account` | Account details & tier info |
| GET | `/v1/usage` | Current month's usage summary |
| GET | `/v1/usage/history` | Detailed usage history |
| GET | `/v1/tiers` | Available pricing tiers |

### Documentation
- **Swagger UI**: https://api.companyrm.lk/docs
- **ReDoc**: https://api.companyrm.lk/redoc

## 📁 Project Structure

```
app/
├── main.py              # Application entry point
├── config.py            # Configuration & tier definitions
├── api/v1/
│   ├── extract.py       # POST /v1/extract endpoint
│   ├── account.py       # Account & usage endpoints
│   └── router.py        # API v1 router
├── db/
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # APIKey, UsageLog models
│   └── crud.py          # Database operations
├── middleware/
│   ├── auth.py          # API key authentication
│   ├── logging.py       # Request logging
│   ├── rate_limiter.py  # Tiered rate limiting
│   └── usage.py         # Usage tracking
├── schemas/
│   ├── extract.py       # Request/response schemas
│   └── errors.py        # Error schemas
└── services/
    ├── extractor.py     # Content extraction logic
    └── billing.py       # Billing & account service
```

## 🔧 Rate Limiting

Every response includes rate limit headers:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 55
X-RateLimit-Limit-Day: 2000
X-RateLimit-Remaining-Day: 1945
```

## 📖 Documentation

- [API Examples](docs/API_EXAMPLES.md) — Request/response examples
- [Deployment Guide](docs/DEPLOYMENT.md) — Nginx & production setup
- [Monetization Guide](docs/MONETIZATION.md) — Pricing & marketing strategy

## 🔗 Integrations

### Python
```python
import requests

response = requests.post(
    "https://api.companyrm.lk/v1/extract",
    headers={"Authorization": "Bearer sk_live_xxx"},
    json={"url": "https://example.com/article"}
)
markdown = response.json()["data"]["markdown"]
```

### LangChain
```python
# Feed clean content directly to your LLM
loader = CleanReaderLoader(api_key="sk_live_xxx")
content = loader.load("https://example.com/article")
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

