# SMM Panel Configuration Guide

## 🔧 Setup Instructions

### Step 1: Get SMM Panel API Keys

You need to register and get API keys from at least one SMM panel:

#### Option 1: PeakSMM (Recommended)
1. Go to https://www.peaksmm.com
2. Register an account
3. Add funds (minimum $10-20)
4. Go to API section
5. Copy your API Key

#### Option 2: JustAnotherPanel
1. Go to https://justanotherpanel.com
2. Register and add funds
3. Find API key in settings

#### Option 3: GlorySMM
1. Go to https://glorysmmpanel.com
2. Register and add funds
3. Get API key from dashboard

### Step 2: Configure Bot

Edit `data/smm_config.json`:

```json
{
  "panels": {
    "peaksmm": {
      "name": "PeakSMM",
      "api_url": "https://www.peaksmm.com/api/v2",
      "api_key": "YOUR_ACTUAL_API_KEY_HERE",
      "enabled": true,
      "priority": 1,
      "min_balance": 5.0
    }
  },
  "service_mapping": {
    "followers": {
      "search_terms": ["followers", "fans"],
      "platform": "tiktok"
    },
    "likes": {
      "search_terms": ["likes", "hearts"],
      "platform": "tiktok"
    },
    "views": {
      "search_terms": ["views", "plays"],
      "platform": "tiktok"
    },
    "shares": {
      "search_terms": ["shares", "reposts"],
      "platform": "tiktok"
    },
    "comments": {
      "search_terms": ["comments"],
      "platform": "tiktok"
    }
  }
}
```

### Step 3: Find Service IDs

Run this test to find available services:

```python
from smm_panel import SMMManager

smm = SMMManager()
for panel_id, panel in smm.panels.items():
    services = panel.get_services()
    for svc in services:
        if 'tiktok' in svc.get('category', '').lower():
            print(f"ID: {svc['service']} | {svc['name']} | ${svc['rate']}")
```

### Step 4: Test the Integration

1. Start the bot: `python bot.py`
2. Send `/admin` to check panel status
3. Try placing a test order
4. Check `data/smm_orders.json` for order tracking

## 📊 API Endpoints Used

### PeakSMM / JustAnotherPanel / GlorySMM (Same Format)

| Action | Parameters | Response |
|--------|-----------|----------|
| **balance** | `key` | `{"balance": 100.50, "currency": "USD"}` |
| **services** | `key` | List of services |
| **add** | `key`, `service`, `url`, `quantity` | `{"order": 12345}` |
| **status** | `key`, `order` | Order details |
| **cancel** | `key`, `order` | Cancellation result |
| **refill** | `key`, `order` | Refill request |

## 💰 Pricing Strategy

### Cost Calculation:
```
Panel Price: $0.50 per 1000 followers
Your Price: $1.00 per 1000 followers
Profit: $0.50 per 1000 (100% markup)
```

### Recommended Markup:
- **Followers**: 100-200% markup
- **Likes**: 50-100% markup
- **Views**: 30-50% markup
- **Comments**: 100-150% markup

## 🔒 Security Tips

1. **Never share API keys**
2. **Use minimum balance checks**
3. **Enable IP whitelist on panel**
4. **Monitor for suspicious orders**
5. **Set daily order limits per user**

## 🚨 Troubleshooting

### "No panel available"
- Check API key is correct
- Verify panel has balance
- Ensure panel is enabled in config

### "Service not found"
- Run service discovery script
- Update search_terms in config
- Check if panel supports TikTok

### "Order failed"
- Check target URL is valid
- Verify quantity is within min/max
- Ensure panel has enough balance

### "Invalid response"
- Check API URL is correct
- Verify panel API version (v2)
- Check internet connection

## 📈 Scaling Tips

1. **Multiple Panels**: Add 2-3 panels for failover
2. **Auto-recharge**: Set up automatic funding
3. **Price monitoring**: Adjust prices based on panel rates
4. **Service rotation**: Use cheapest available panel
5. **Bulk discounts**: Negotiate with panels for volume

## 🔄 Advanced Features

### Automatic Failover:
```python
# If Panel 1 fails, automatically uses Panel 2
panel1 = PeakSMM(api_key1)  # Primary
panel2 = JAP(api_key2)      # Backup
```

### Dynamic Pricing:
```python
# Adjust prices based on panel costs
def get_price(service_type):
    panel = smm_manager.get_best_panel(service_type)
    rate = float(panel[2]['rate'])
    return rate * 1.5  # 50% markup
```

### Order Distribution:
```python
# Split large orders across panels
if quantity > 10000:
    order1 = panel1.place_order(url, 5000)
    order2 = panel2.place_order(url, 5000)
```

## 📞 Support

For issues:
1. Check logs in `logs/bot.log`
2. Verify panel API docs
3. Test API calls manually
4. Contact panel support

---

**Ready to start?** Add your API keys and run the bot!
