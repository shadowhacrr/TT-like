# Complete SMM Panel Configuration
# Top providers: Peakerr, BulkFollows, AirSMM, Top4SMM, MoreThanPanel

SMM_PANELS = {
    # Primary Panel - Peakerr (Recommended for TikTok)
    "peakerr": {
        "name": "Peakerr",
        "api_url": "https://www.peakerr.com/api/v2",
        "api_key": "YOUR_PEAKERR_API_KEY",
        "enabled": False,  # Set to True after adding API key
        "priority": 1,
        "min_balance": 1.0,
        "payment_methods": ["PayPal", "Crypto", "Cards", "bKash", "PayTM"],
        "features": ["refill", "cancel", "bulk_orders"]
    },

    # Secondary Panel - BulkFollows (Cheap rates)
    "bulkfollows": {
        "name": "BulkFollows",
        "api_url": "https://bulkfollows.com/api/v2",
        "api_key": "YOUR_BULKFOLLOWS_API_KEY",
        "enabled": False,
        "priority": 2,
        "min_balance": 1.0,
        "payment_methods": ["PayPal", "Paytm", "Crypto", "JazzCash", "bKash"],
        "features": ["refill", "24_7_support"]
    },

    # Tertiary Panel - AirSMM (Fast delivery)
    "airsmm": {
        "name": "AirSMM",
        "api_url": "https://airsmm.com/api/v2",
        "api_key": "YOUR_AIRSMM_API_KEY",
        "enabled": False,
        "priority": 3,
        "min_balance": 1.0,
        "payment_methods": ["PayPal", "Crypto", "Cards"],
        "features": ["fast_delivery", "api_access"]
    },

    # Backup Panel - Top4SMM (Lifetime guarantee)
    "top4smm": {
        "name": "Top4SMM",
        "api_url": "https://top4smm.com/api/v2",
        "api_key": "YOUR_TOP4SMM_API_KEY",
        "enabled": False,
        "priority": 4,
        "min_balance": 1.0,
        "payment_methods": ["Cards", "Crypto", "Apple Pay", "Google Pay"],
        "features": ["lifetime_guarantee", "smart_delivery"]
    }
}

# Service Mapping - TikTok Services
# These are example service IDs - actual IDs will be fetched from panels
SERVICE_MAPPING = {
    "tiktok_followers": {
        "search_terms": ["TikTok Followers", "TT Followers", "TikTok Fans"],
        "min": 50,
        "max": 100000,
        "default": 1000
    },
    "tiktok_likes": {
        "search_terms": ["TikTok Likes", "TT Likes", "TikTok Hearts"],
        "min": 100,
        "max": 500000,
        "default": 1000
    },
    "tiktok_views": {
        "search_terms": ["TikTok Views", "TT Views", "TikTok Video Views"],
        "min": 1000,
        "max": 10000000,
        "default": 5000
    },
    "tiktok_shares": {
        "search_terms": ["TikTok Shares", "TT Shares", "TikTok Reposts"],
        "min": 50,
        "max": 50000,
        "default": 500
    },
    "tiktok_comments": {
        "search_terms": ["TikTok Comments", "TT Comments", "Custom Comments"],
        "min": 10,
        "max": 10000,
        "default": 50
    }
}

# Pricing Strategy (your markup over panel cost)
PRICING = {
    "markup_percent": 50,  # 50% profit margin
    "min_order_value": 0.10,  # $0.10 minimum
    "currency": "USD"
}

# Order Settings
ORDER_SETTINGS = {
    "auto_retry": True,
    "max_retries": 3,
    "status_check_interval": 60,  # seconds
    "auto_refill": True,
    "refill_threshold": 10  # refill if drops below 10%
}
