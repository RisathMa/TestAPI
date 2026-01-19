# API Monetization Guide

## Pricing Tiers

| Tier | Monthly Requests | Rate Limit | Price | Best For |
|------|------------------|------------|-------|----------|
| **Free** | 100 | 10/min | $0 | Testing & evaluation |
| **Developer** | 5,000 | 60/min | $7.50/mo | Side projects, MVPs |
| **Pro** | 25,000 | 300/min | $30/mo | Production apps |
| **Business** | 100,000 | 1000/min | $100/mo | High-traffic services |
| **Enterprise** | Unlimited | Custom | Contact us | Mission-critical apps |

## Pay-Per-Use Pricing

| Request Type | Cost |
|-------------|------|
| Base extraction (≤500KB) | $0.0015 |
| Large page (>500KB) | +$0.001 |
| Image extraction | +$0.002 |
| PDF extraction | +$0.003 |

### Tier Discounts
- **Pro**: 10% off all requests
- **Business**: 30% off all requests  
- **Enterprise**: 40% off all requests

---

## API Endpoints

### Account & Usage

```bash
# Get account status
curl -X GET https://api.companyrm.lk/v1/account \
  -H "Authorization: Bearer sk_live_your_key"

# Get usage summary
curl -X GET https://api.companyrm.lk/v1/usage \
  -H "Authorization: Bearer sk_live_your_key"

# Get usage history
curl -X GET "https://api.companyrm.lk/v1/usage/history?limit=50" \
  -H "Authorization: Bearer sk_live_your_key"

# Get tier comparison
curl -X GET https://api.companyrm.lk/v1/tiers \
  -H "Authorization: Bearer sk_live_your_key"
```

### Response Examples

#### Account Status
```json
{
  "success": true,
  "data": {
    "account": {
      "tier": "developer",
      "tier_name": "Developer",
      "is_active": true,
      "features": ["All Free features", "Priority support", "Higher rate limits"]
    },
    "usage": {
      "requests_this_month": 1250,
      "monthly_limit": 5000,
      "usage_percentage": 25.0,
      "remaining": 3750
    },
    "billing": {
      "current_month_cost_usd": 1.875,
      "price_per_request": 0.0015,
      "tier_discount": "0%"
    },
    "rate_limits": {
      "per_minute": 60,
      "per_day": 2000
    },
    "alerts": []
  }
}
```

---

## Abuse Prevention

### Rate Limiting
- Per-minute limits enforced via sliding window
- Per-day limits for sustained usage control
- Monthly quotas with warning alerts at 80%

### Headers Returned
```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 55
X-RateLimit-Limit-Day: 2000
X-RateLimit-Remaining-Day: 1945
```

### Rate Limit Response (429)
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 60 requests per minute",
    "billable": false
  }
}
```

---

## Marketing Channels (No Ads/UI Required)

### Primary Platforms
1. **RapidAPI** - List your API, they handle billing
2. **API Layer** - Similar marketplace
3. **Public APIs GitHub** - Submit PR for visibility
4. **Programmable Web** - API directory

### Developer Communities
1. **r/LocalLLaMA** - LLM developers
2. **r/MachineLearning** - ML practitioners  
3. **LangChain Discord** - AI tooling users
4. **Hacker News** - "Show HN" launch

### Content Marketing
1. Write "How to feed clean web content to LLMs" on Dev.to
2. Create LangChain/LlamaIndex integration examples
3. Publish OpenAPI spec for auto-generated SDKs

---

## Integration Examples

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

### LangChain Loader
```python
from langchain.document_loaders import WebBaseLoader

class CleanReaderLoader(WebBaseLoader):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def load(self, url: str):
        response = requests.post(
            "https://api.companyrm.lk/v1/extract",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"url": url}
        )
        return response.json()["data"]["markdown"]
```

### Node.js
```javascript
const response = await fetch("https://api.cleanreader.com/v1/extract", {
  method: "POST",
  headers: {
    "Authorization": "Bearer sk_live_xxx",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ url: "https://example.com/article" })
});
const { data } = await response.json();
console.log(data.markdown);
```

---

## Revenue Projections

| Growth Stage | Paid Users | Avg Requests | Monthly Revenue |
|--------------|------------|--------------|-----------------|
| Launch (Month 1-3) | 20 | 2,000 | $60 |
| Growth (Month 4-6) | 100 | 5,000 | $750 |
| Mature (Month 7-12) | 300 | 10,000 | $2,250 |
| Scale (Year 2) | 1,000 | 25,000 | $7,500 |

### Key Metrics to Track
- Free → Paid conversion rate (target: 5-10%)
- Average requests per user
- Churn rate (target: <5% monthly)
- Customer acquisition cost (CAC)
- Lifetime value (LTV)
