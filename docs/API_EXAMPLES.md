# API Examples

Example requests and responses for the Clean Reader API.

---

## Authentication

All requests require an API key in the Authorization header:

```
Authorization: Bearer sk_live_your_api_key
```

---

## POST /v1/extract

### Basic Request

```bash
curl -X POST https://apis.companyrm.lk/v1/extract \
  -H "Authorization: Bearer sk_test_demo_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

### Success Response

```json
{
  "success": true,
  "request_id": "req_a1b2c3d4e5f6",
  "url": "https://example.com",
  "extracted_at": "2026-01-19T14:23:45Z",
  "content": {
    "markdown": "# Example Domain\n\nThis domain is for use in illustrative examples in documents...",
    "text_length": 1256,
    "estimated_tokens": 314
  },
  "metadata": {
    "title": "Example Domain",
    "author": null,
    "published_date": null,
    "site_name": null,
    "excerpt": "This domain is for use in illustrative examples",
    "lang": "en"
  },
  "images": null,
  "usage": {
    "billable_units": 1,
    "cost_usd": 0.0015
  }
}
```

---

### Full Options Request

```bash
curl -X POST https://apis.companyrm.lk/v1/extract \
  -H "Authorization: Bearer sk_test_demo_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "options": {
      "include_images": true,
      "include_metadata": true,
      "markdown_flavor": "github",
      "max_content_length": 50000,
      "timeout_ms": 10000
    }
  }'
```

### Response with Images

```json
{
  "success": true,
  "request_id": "req_xyz789abc",
  "url": "https://example.com/article",
  "extracted_at": "2026-01-19T14:25:00Z",
  "content": {
    "markdown": "# Article Title\n\n![Hero Image](https://example.com/hero.jpg)\n\nArticle content here...",
    "text_length": 12450,
    "estimated_tokens": 3112
  },
  "metadata": {
    "title": "Article Title",
    "author": "Jane Doe",
    "published_date": "2026-01-15",
    "site_name": "Example News",
    "excerpt": "Brief summary of the article...",
    "lang": "en"
  },
  "images": [
    {
      "url": "https://example.com/hero.jpg",
      "alt": "Hero image description",
      "position": "top"
    },
    {
      "url": "https://example.com/chart.png",
      "alt": "Data chart",
      "position": "middle"
    }
  ],
  "usage": {
    "billable_units": 1,
    "cost_usd": 0.0035
  }
}
```

---

## Error Responses

### Invalid API Key

```bash
curl -X POST https://apis.companyrm.lk/v1/extract \
  -H "Authorization: Bearer invalid_key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

```json
{
  "success": false,
  "request_id": "req_err123",
  "error": {
    "code": "INVALID_API_KEY",
    "message": "Invalid API key",
    "billable": false
  }
}
```

### Fetch Timeout

```json
{
  "success": false,
  "request_id": "req_timeout456",
  "error": {
    "code": "FETCH_TIMEOUT",
    "message": "Target URL took >5000ms to respond",
    "billable": false
  }
}
```

### Rate Limit Exceeded

```json
{
  "success": false,
  "request_id": "req_limit789",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Monthly request limit exceeded",
    "billable": false
  }
}
```

---

## Python SDK Example

```python
import requests

API_KEY = "sk_live_your_api_key"
BASE_URL = "https://apis.companyrm.lk"

def extract_url(url: str, include_images: bool = False) -> dict:
    """Extract clean content from a URL."""
    response = requests.post(
        f"{BASE_URL}/v1/extract",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "url": url,
            "options": {
                "include_images": include_images,
                "include_metadata": True
            }
        }
    )
    return response.json()

# Usage
result = extract_url("https://example.com/article")

if result["success"]:
    markdown = result["content"]["markdown"]
    tokens = result["content"]["estimated_tokens"]
    print(f"Extracted {tokens} tokens")
    print(markdown[:500])
else:
    print(f"Error: {result['error']['message']}")
```

---

## Integration with LLMs

```python
import openai

# Extract article
article = extract_url("https://news.example.com/tech-article")

if article["success"]:
    # Feed clean content to GPT-4
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize articles concisely."},
            {"role": "user", "content": article["content"]["markdown"]}
        ]
    )
    summary = response.choices[0].message.content
    print(summary)
```
