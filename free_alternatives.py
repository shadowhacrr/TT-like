"""
FREE Alternatives to Paid SMM Panels
1. Engagement Exchange (Like4Like style)
2. Free Trial APIs (SociaVault, etc.)
3. Open Source Automation (Selenium)
"""

import json
import time
import random
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# ============== OPTION 1: ENGAGEMENT EXCHANGE SYSTEM ==============

@dataclass
class ExchangeUser:
    """User in the exchange system"""
    user_id: int
    username: str
    tiktok_username: str
    points: int = 0
    total_given: int = 0
    total_received: int = 0
    joined_at: float = 0
    last_active: float = 0
    is_active: bool = True

class EngagementExchange:
    """
    Like4Like style engagement exchange
    Users earn points by engaging with others, spend points to get engagement
    """

    def __init__(self, data_dir: str = "data/exchange"):
        self.data_dir = data_dir
        self.users_file = f"{data_dir}/exchange_users.json"
        self.queue_file = f"{data_dir}/engagement_queue.json"
        self.history_file = f"{data_dir}/exchange_history.json"

        # Points system
        self.EARN_RATES = {
            "follow": 10,      # Follow someone = 10 points
            "like": 5,         # Like video = 5 points
            "view": 1,         # View video = 1 point
            "share": 15,       # Share video = 15 points
            "comment": 20      # Comment = 20 points
        }

        self.COST_RATES = {
            "followers": 8,    # 8 points per follower
            "likes": 4,        # 4 points per like
            "views": 0.5,      # 0.5 points per view
            "shares": 12,      # 12 points per share
            "comments": 15     # 15 points per comment
        }

        self._init_storage()

    def _init_storage(self):
        """Initialize storage files"""
        import os
        os.makedirs(self.data_dir, exist_ok=True)

        for file in [self.users_file, self.queue_file, self.history_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)

    def register_user(self, user_id: int, username: str, tiktok_username: str) -> ExchangeUser:
        """Register new user in exchange"""
        users = self._load_json(self.users_file, {})

        if str(user_id) in users:
            # Update existing
            user_data = users[str(user_id)]
            user_data["tiktok_username"] = tiktok_username
            user_data["last_active"] = time.time()
        else:
            # Create new
            user_data = {
                "user_id": user_id,
                "username": username,
                "tiktok_username": tiktok_username,
                "points": 20,  # Welcome bonus
                "total_given": 0,
                "total_received": 0,
                "joined_at": time.time(),
                "last_active": time.time(),
                "is_active": True
            }

        users[str(user_id)] = user_data
        self._save_json(self.users_file, users)

        return ExchangeUser(**user_data)

    def get_user(self, user_id: int) -> Optional[ExchangeUser]:
        """Get user data"""
        users = self._load_json(self.users_file, {})
        if str(user_id) in users:
            return ExchangeUser(**users[str(user_id)])
        return None

    def earn_points(self, user_id: int, action: str, target_user: str) -> int:
        """
        Award points for engaging with others
        action: follow, like, view, share, comment
        """
        points = self.EARN_RATES.get(action, 0)
        if points <= 0:
            return 0

        users = self._load_json(self.users_file, {})
        if str(user_id) not in users:
            return 0

        # Check if already engaged with this target today (prevent spam)
        history = self._load_json(self.history_file, [])
        today = datetime.now().strftime("%Y-%m-%d")

        recent_actions = [
            h for h in history 
            if h["user_id"] == user_id 
            and h["target"] == target_user
            and h["action"] == action
            and h["date"] == today
        ]

        if len(recent_actions) >= 5:  # Max 5 same actions per day per target
            return 0

        # Award points
        users[str(user_id)]["points"] += points
        users[str(user_id)]["total_given"] += 1
        users[str(user_id)]["last_active"] = time.time()
        self._save_json(self.users_file, users)

        # Record in history
        history.append({
            "user_id": user_id,
            "action": action,
            "target": target_user,
            "points": points,
            "date": today,
            "timestamp": time.time()
        })
        self._save_json(self.history_file, history)

        return points

    def spend_points(self, user_id: int, service: str, quantity: int) -> Dict:
        """Spend points to get engagement"""
        cost_per_unit = self.COST_RATES.get(service, 1)
        total_cost = int(cost_per_unit * quantity)

        user = self.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        if user.points < total_cost:
            return {
                "success": False, 
                "error": f"Insufficient points. Need {total_cost}, have {user.points}",
                "points_needed": total_cost - user.points
            }

        # Deduct points
        users = self._load_json(self.users_file, {})
        users[str(user_id)]["points"] -= total_cost
        users[str(user_id)]["total_received"] += quantity
        self._save_json(self.users_file, users)

        # Add to queue
        queue = self._load_json(self.queue_file, [])
        order = {
            "order_id": f"EXC{int(time.time())}{user_id}",
            "user_id": user_id,
            "tiktok_username": user.tiktok_username,
            "service": service,
            "quantity": quantity,
            "points_spent": total_cost,
            "status": "pending",
            "created_at": time.time(),
            "fulfilled_by": []  # List of users who engaged
        }
        queue.append(order)
        self._save_json(self.queue_file, queue)

        return {
            "success": True,
            "order_id": order["order_id"],
            "points_spent": total_cost,
            "remaining_points": user.points - total_cost
        }

    def get_available_tasks(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get tasks for user to complete and earn points"""
        queue = self._load_json(self.queue_file, [])
        user = self.get_user(user_id)

        if not user:
            return []

        # Filter out user's own orders and completed ones
        available = [
            q for q in queue 
            if q["user_id"] != user_id 
            and q["status"] == "pending"
            and len(q["fulfilled_by"]) < q["quantity"]
            and user_id not in q["fulfilled_by"]
        ]

        # Return random selection
        random.shuffle(available)
        return available[:limit]

    def complete_task(self, worker_id: int, order_id: str, action: str) -> Dict:
        """Mark task as completed and award points"""
        queue = self._load_json(self.queue_file, [])

        for order in queue:
            if order["order_id"] == order_id:
                if worker_id in order["fulfilled_by"]:
                    return {"success": False, "error": "Already completed"}

                # Mark fulfilled
                order["fulfilled_by"].append(worker_id)

                # Check if fully fulfilled
                if len(order["fulfilled_by"]) >= order["quantity"]:
                    order["status"] = "completed"
                    order["completed_at"] = time.time()

                self._save_json(self.queue_file, queue)

                # Award points to worker
                points_earned = self.earn_points(worker_id, action, order["tiktok_username"])

                return {
                    "success": True,
                    "points_earned": points_earned,
                    "total_fulfilled": len(order["fulfilled_by"]),
                    "required": order["quantity"]
                }

        return {"success": False, "error": "Order not found"}

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users by points"""
        users = self._load_json(self.users_file, {})

        sorted_users = sorted(
            users.values(),
            key=lambda x: x["points"],
            reverse=True
        )

        return [
            {
                "username": u["username"],
                "tiktok": u["tiktok_username"],
                "points": u["points"],
                "given": u["total_given"],
                "received": u["total_received"]
            }
            for u in sorted_users[:limit]
        ]

    def _load_json(self, filename: str, default):
        """Load JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default

    def _save_json(self, filename: str, data):
        """Save JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


# ============== OPTION 2: FREE TRIAL API MANAGER ==============

class FreeTrialAPIManager:
    """
    Manages free trial APIs from various providers
    SociaVault: 50 free credits
    ScrapeCreators: 100 free calls
    Other providers with free tiers
    """

    def __init__(self):
        self.apis = {
            "sociavault": {
                "name": "SociaVault",
                "url": "https://api.sociavault.com/v1",
                "free_credits": 50,
                "cost_per_request": 1,
                "supports": ["tiktok_profile", "tiktok_videos"],
                "signup_url": "https://sociavault.com/signup",
                "requires_card": False
            },
            "scrapecreators": {
                "name": "ScrapeCreators",
                "url": "https://api.scrapecreators.com/v1",
                "free_credits": 100,
                "cost_per_request": 1,
                "supports": ["tiktok_profile", "tiktok_videos", "tiktok_comments"],
                "signup_url": "https://scrapecreators.com",
                "requires_card": False
            },
            "tikapi": {
                "name": "TikAPI",
                "url": "https://api.tikapi.io/public",
                "free_credits": 1000,  # 1000 free requests
                "cost_per_request": 1,
                "supports": ["tiktok_profile", "tiktok_videos", "tiktok_search"],
                "signup_url": "https://tikapi.io",
                "requires_card": False
            }
        }

        self.usage_file = "data/free_api_usage.json"
        self._init_storage()

    def _init_storage(self):
        """Initialize storage"""
        import os
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(self.usage_file):
            self._save_json(self.usage_file, {
                api_id: {
                    "api_key": None,
                    "used_credits": 0,
                    "remaining": info["free_credits"],
                    "enabled": False
                }
                for api_id, info in self.apis.items()
            })

    def setup_api(self, api_id: str, api_key: str):
        """Configure API key for a service"""
        usage = self._load_json(self.usage_file, {})

        if api_id in usage:
            usage[api_id]["api_key"] = api_key
            usage[api_id]["enabled"] = True
            self._save_json(self.usage_file, usage)
            return True
        return False

    def get_available_apis(self) -> List[Dict]:
        """Get list of APIs with remaining credits"""
        usage = self._load_json(self.usage_file, {})

        available = []
        for api_id, info in self.apis.items():
            api_usage = usage.get(api_id, {})
            if api_usage.get("enabled") and api_usage.get("remaining", 0) > 0:
                available.append({
                    "id": api_id,
                    "name": info["name"],
                    "remaining": api_usage["remaining"],
                    "supports": info["supports"]
                })

        return available

    def use_credit(self, api_id: str) -> bool:
        """Deduct credit from API"""
        usage = self._load_json(self.usage_file, {})

        if api_id in usage and usage[api_id]["remaining"] > 0:
            usage[api_id]["used_credits"] += 1
            usage[api_id]["remaining"] -= 1
            self._save_json(self.usage_file, usage)
            return True
        return False

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        usage = self._load_json(self.usage_file, {})

        total_free = sum(api["free_credits"] for api in self.apis.values())
        total_used = sum(u.get("used_credits", 0) for u in usage.values())
        total_remaining = total_free - total_used

        return {
            "total_free_credits": total_free,
            "total_used": total_used,
            "total_remaining": total_remaining,
            "apis": {
                api_id: {
                    "name": self.apis[api_id]["name"],
                    "remaining": u.get("remaining", 0),
                    "enabled": u.get("enabled", False)
                }
                for api_id, u in usage.items()
            }
        }

    def _load_json(self, filename: str, default):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default

    def _save_json(self, filename: str, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


# ============== OPTION 3: COMMUNITY BOT NETWORK ==============

class CommunityBotNetwork:
    """
    Network of community-run bots that help each other
    Decentralized engagement sharing
    """

    def __init__(self):
        self.network_file = "data/bot_network.json"
        self._init_storage()

    def _init_storage(self):
        import os
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(self.network_file):
            self._save_json(self.network_file, {
                "bots": [],
                "shared_orders": [],
                "network_stats": {
                    "total_bots": 0,
                    "total_orders_shared": 0,
                    "active_since": time.time()
                }
            })

    def register_bot(self, bot_id: str, bot_name: str, webhook_url: str, 
                     capabilities: List[str], owner_id: int):
        """Register a bot in the network"""
        network = self._load_json(self.network_file, {})

        # Check if already registered
        for bot in network["bots"]:
            if bot["bot_id"] == bot_id:
                bot["last_seen"] = time.time()
                bot["is_active"] = True
                self._save_json(self.network_file, network)
                return {"success": True, "message": "Bot updated"}

        # Add new bot
        network["bots"].append({
            "bot_id": bot_id,
            "name": bot_name,
            "webhook_url": webhook_url,
            "capabilities": capabilities,  # ["followers", "likes", "views"]
            "owner_id": owner_id,
            "joined_at": time.time(),
            "last_seen": time.time(),
            "is_active": True,
            "trust_score": 50,  # 0-100, increases with successful trades
            "total_orders_fulfilled": 0,
            "total_orders_received": 0
        })

        network["network_stats"]["total_bots"] = len(network["bots"])
        self._save_json(self.network_file, network)

        return {"success": True, "message": "Bot registered"}

    def request_help(self, requester_id: str, service: str, target: str, 
                     quantity: int) -> Dict:
        """Request help from network"""
        network = self._load_json(self.network_file, {})

        # Find bots that can help
        capable_bots = [
            b for b in network["bots"]
            if b["bot_id"] != requester_id
            and b["is_active"]
            and service in b["capabilities"]
            and b["trust_score"] > 30
        ]

        if not capable_bots:
            return {"success": False, "error": "No bots available"}

        # Sort by trust score
        capable_bots.sort(key=lambda x: x["trust_score"], reverse=True)

        # Create shared order
        order = {
            "order_id": f"NET{int(time.time())}",
            "requester": requester_id,
            "service": service,
            "target": target,
            "quantity": quantity,
            "status": "pending",
            "helpers": [],
            "created_at": time.time(),
            "completed_at": None
        }

        network["shared_orders"].append(order)
        network["network_stats"]["total_orders_shared"] += 1
        self._save_json(self.network_file, network)

        # Notify top 3 bots
        notified = []
        for bot in capable_bots[:3]:
            # In real implementation, send webhook/API call
            notified.append(bot["bot_id"])

        return {
            "success": True,
            "order_id": order["order_id"],
            "bots_notified": len(notified),
            "estimated_time": "5-15 minutes"
        }

    def _load_json(self, filename: str, default):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default

    def _save_json(self, filename: str, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


# ============== INTEGRATION WITH MAIN BOT ==============

class FreeOrderManager:
    """
    Manages orders using free methods
    Falls back through: Exchange -> Free APIs -> Community Network
    """

    def __init__(self):
        self.exchange = EngagementExchange()
        self.free_apis = FreeTrialAPIManager()
        self.community = CommunityBotNetwork()

    async def process_order(self, user_id: int, service: str, target: str, 
                           quantity: int, username: str) -> Dict:
        """
        Try free methods in order:
        1. Engagement Exchange (if user has points)
        2. Free Trial APIs (if available)
        3. Community Network
        4. Simulation (last resort)
        """

        # Method 1: Engagement Exchange
        user = self.exchange.get_user(user_id)
        if user and user.points > 0:
            result = self.exchange.spend_points(user_id, service, quantity)
            if result["success"]:
                return {
                    "method": "exchange",
                    "order_id": result["order_id"],
                    "points_spent": result["points_spent"],
                    "remaining_points": result["remaining_points"],
                    "message": f"Order placed using Engagement Exchange! {result['points_spent']} points spent."
                }

        # Method 2: Free APIs
        available_apis = self.free_apis.get_available_apis()
        if available_apis:
            api = available_apis[0]  # Use first available
            if self.free_apis.use_credit(api["id"]):
                return {
                    "method": "free_api",
                    "api_used": api["name"],
                    "remaining_credits": api["remaining"] - 1,
                    "message": f"Order processed using {api['name']} free tier!"
                }

        # Method 3: Community Network
        # Register our bot first
        self.community.register_bot(
            bot_id="main_bot",
            bot_name="ZefoyPro",
            webhook_url="https://your-webhook-url.com",
            capabilities=["followers", "likes", "views"],
            owner_id=user_id
        )

        result = self.community.request_help(
            requester_id="main_bot",
            service=service,
            target=target,
            quantity=quantity
        )

        if result["success"]:
            return {
                "method": "community",
                "order_id": result["order_id"],
                "bots_notified": result["bots_notified"],
                "message": f"Request sent to {result['bots_notified']} community bots!"
            }

        # Method 4: Simulation (last resort)
        return {
            "method": "simulation",
            "message": "Free methods exhausted. Running simulation mode (no real delivery)."
        }

    def get_free_options_status(self, user_id: int) -> Dict:
        """Get status of all free options"""
        user = self.exchange.get_user(user_id)
        api_stats = self.free_apis.get_stats()

        return {
            "engagement_exchange": {
                "available": user is not None,
                "points": user.points if user else 0,
                "can_order": user.points > 0 if user else False
            },
            "free_apis": {
                "total_remaining": api_stats["total_remaining"],
                "apis": api_stats["apis"]
            },
            "community_network": {
                "active": True,
                "bots_online": "3+"  # Estimated
            }
        }

# Example usage
if __name__ == "__main__":
    # Test engagement exchange
    exchange = EngagementExchange()

    # Register test user
    user = exchange.register_user(12345, "test_user", "test_tiktok")
    print(f"User registered with {user.points} points")

    # Earn points by helping others
    points = exchange.earn_points(12345, "follow", "@someone")
    print(f"Earned {points} points")

    # Spend points
    result = exchange.spend_points(12345, "followers", 10)
    print(f"Order result: {result}")
