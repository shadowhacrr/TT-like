import json
import os
import time
import random
from datetime import datetime, timedelta
from config import (
    USERS_FILE, ORDERS_FILE, COOLDOWNS_FILE, STATS_FILE,
    SERVICES, ERROR_MESSAGES, DATA_DIR
)

class FileStorage:
    """File-based JSON storage system"""

    @staticmethod
    def load_json(filename, default=None):
        """Load data from JSON file"""
        if default is None:
            default = {}
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default

    @staticmethod
    def save_json(filename, data):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            return False

class UserManager:
    """Manage user data"""

    @staticmethod
    def get_user(user_id):
        """Get user data"""
        users = FileStorage.load_json(USERS_FILE, {})
        return users.get(str(user_id), {})

    @staticmethod
    def save_user(user_id, user_data):
        """Save user data"""
        users = FileStorage.load_json(USERS_FILE, {})
        users[str(user_id)] = user_data
        FileStorage.save_json(USERS_FILE, users)

    @staticmethod
    def register_user(user_id, username, first_name, last_name):
        """Register new user"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "joined_date": datetime.now().isoformat(),
            "total_orders": 0,
            "last_activity": datetime.now().isoformat(),
            "is_banned": False,
            "language": "en"
        }
        UserManager.save_user(user_id, user_data)
        StatsManager.increment_stat("total_users")
        return user_data

    @staticmethod
    def update_activity(user_id):
        """Update user last activity"""
        user = UserManager.get_user(user_id)
        if user:
            user["last_activity"] = datetime.now().isoformat()
            UserManager.save_user(user_id, user)

    @staticmethod
    def get_total_users():
        """Get total registered users"""
        users = FileStorage.load_json(USERS_FILE, {})
        return len(users)

class OrderManager:
    """Manage orders"""

    @staticmethod
    def create_order(user_id, service_type, target, quantity, status="pending"):
        """Create new order"""
        orders = FileStorage.load_json(ORDERS_FILE, [])

        order_id = f"ORD{int(time.time())}{random.randint(1000, 9999)}"
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "service": service_type,
            "target": target,
            "quantity": quantity,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "delivery_time": random.randint(300, 1800)  # 5-30 minutes
        }

        orders.append(order)
        FileStorage.save_json(ORDERS_FILE, orders)

        # Update user stats
        user = UserManager.get_user(user_id)
        if user:
            user["total_orders"] = user.get("total_orders", 0) + 1
            UserManager.save_user(user_id, user)

        StatsManager.increment_stat("total_orders")
        StatsManager.increment_stat(f"{service_type}_orders")

        return order

    @staticmethod
    def get_user_orders(user_id, limit=10):
        """Get user's recent orders"""
        orders = FileStorage.load_json(ORDERS_FILE, [])
        user_orders = [o for o in orders if o["user_id"] == user_id]
        return sorted(user_orders, key=lambda x: x["created_at"], reverse=True)[:limit]

    @staticmethod
    def get_total_orders():
        """Get total orders count"""
        orders = FileStorage.load_json(ORDERS_FILE, [])
        return len(orders)

    @staticmethod
    def update_order_status(order_id, status):
        """Update order status"""
        orders = FileStorage.load_json(ORDERS_FILE, [])
        for order in orders:
            if order["order_id"] == order_id:
                order["status"] = status
                if status == "completed":
                    order["completed_at"] = datetime.now().isoformat()
                FileStorage.save_json(ORDERS_FILE, orders)
                return True
        return False

class CooldownManager:
    """Manage service cooldowns"""

    @staticmethod
    def get_cooldown(user_id, service_type):
        """Get remaining cooldown time"""
        cooldowns = FileStorage.load_json(COOLDOWNS_FILE, {})
        user_cooldowns = cooldowns.get(str(user_id), {})
        service_cooldown = user_cooldowns.get(service_type, 0)

        remaining = service_cooldown - time.time()
        return max(0, remaining)

    @staticmethod
    def set_cooldown(user_id, service_type):
        """Set cooldown for service"""
        cooldowns = FileStorage.load_json(COOLDOWNS_FILE, {})

        if str(user_id) not in cooldowns:
            cooldowns[str(user_id)] = {}

        service_config = SERVICES.get(service_type, {})
        cooldown_duration = service_config.get("cooldown", 3600)

        cooldowns[str(user_id)][service_type] = time.time() + cooldown_duration
        FileStorage.save_json(COOLDOWNS_FILE, cooldowns)

    @staticmethod
    def format_time(seconds):
        """Format seconds to readable time"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds/60)} minutes"
        else:
            hours = int(seconds/3600)
            minutes = int((seconds % 3600)/60)
            return f"{hours}h {minutes}m"

class StatsManager:
    """Manage bot statistics"""

    @staticmethod
    def get_stats():
        """Get all stats"""
        return FileStorage.load_json(STATS_FILE, {
            "total_users": 0,
            "total_orders": 0,
            "followers_orders": 0,
            "likes_orders": 0,
            "views_orders": 0,
            "shares_orders": 0,
            "comments_orders": 0,
            "start_time": datetime.now().isoformat()
        })

    @staticmethod
    def increment_stat(key, value=1):
        """Increment a stat"""
        stats = StatsManager.get_stats()
        stats[key] = stats.get(key, 0) + value
        FileStorage.save_json(STATS_FILE, stats)

    @staticmethod
    def get_formatted_stats():
        """Get formatted stats for display"""
        stats = StatsManager.get_stats()
        return {
            "total_users": f"{stats.get('total_users', 0):,}",
            "total_orders": f"{stats.get('total_orders', 0):,}",
            "uptime": StatsManager.get_uptime()
        }

    @staticmethod
    def get_uptime():
        """Calculate bot uptime"""
        stats = StatsManager.get_stats()
        start = datetime.fromisoformat(stats.get("start_time", datetime.now().isoformat()))
        uptime = datetime.now() - start
        days = uptime.days
        hours = uptime.seconds // 3600
        return f"{days}d {hours}h"

class TikTokValidator:
    """Validate TikTok usernames and links"""

    @staticmethod
    def validate_username(username):
        """Validate TikTok username"""
        # Remove @ if present
        username = username.strip().replace("@", "")

        # Basic validation: 2-24 chars, alphanumeric + underscore + period
        if not username:
            return False, "Empty username"
        if len(username) < 2 or len(username) > 24:
            return False, "Username must be 2-24 characters"
        if not all(c.isalnum() or c in "_." for c in username):
            return False, "Invalid characters in username"

        return True, username

    @staticmethod
    def validate_video_link(link):
        """Validate TikTok video link"""
        valid_domains = [
            "tiktok.com",
            "vm.tiktok.com",
            "vt.tiktok.com",
            "m.tiktok.com"
        ]

        link = link.strip().lower()

        # Check if it's a valid TikTok domain
        if not any(domain in link for domain in valid_domains):
            return False, "Invalid TikTok link"

        # Check for video ID pattern (simplified)
        if "/video/" in link or "/t/" in link or "/v/" in link:
            return True, link

        return False, "Invalid video link format"

    @staticmethod
    def extract_username_from_link(link):
        """Extract username from TikTok link"""
        # Simplified extraction
        try:
            if "@" in link:
                parts = link.split("@")
                if len(parts) > 1:
                    username = parts[1].split("/")[0]
                    return username
            return None
        except:
            return None

class OrderSimulator:
    """Simulate order processing (since we don't have real TikTok API)"""

    @staticmethod
    def simulate_processing(service_type, quantity):
        """Simulate order processing steps"""
        steps = [
            ("🔍", "Validating TikTok account...", 10),
            ("📡", "Connecting to TikTok servers...", 25),
            ("⚡", f"Preparing {quantity:,} {service_type}...", 40),
            ("🚀", "Initiating delivery sequence...", 60),
            ("⏳", "Processing delivery...", 80),
            ("✅", "Finalizing order...", 95),
            ("🎉", "Order completed successfully!", 100)
        ]
        return steps

    @staticmethod
    def generate_success_message(service_type, quantity, target):
        """Generate success message"""
        messages = [
            f"🎉 *Success!* {quantity:,} {service_type} have been sent to `{target}`!",
            f"✅ *Delivered!* Your {service_type} are on the way to `{target}`!",
            f"🚀 *Completed!* {quantity:,} {service_type} successfully queued for `{target}`!"
        ]
        return random.choice(messages)

    @staticmethod
    def get_delivery_time():
        """Get random delivery time"""
        minutes = random.randint(5, 30)
        return f"~{minutes} minutes"
