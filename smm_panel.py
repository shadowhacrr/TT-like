"""
SMM Panel Integration Module - Real API Implementation
Supports: PeakSMM, JustAnotherPanel, GlorySMM (all use same API format)
"""

import json
import requests
import time
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ERROR = "error"
    REFUNDED = "refunded"

@dataclass
class SMMOrder:
    """Order data structure"""
    order_id: str
    external_id: Optional[str]
    service: str
    target: str
    quantity: int
    status: OrderStatus
    price: float
    created_at: float
    updated_at: float
    provider: str
    charge: float = 0.0
    start_count: int = 0
    remains: int = 0
    currency: str = "USD"
    response_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'SMMOrder':
        """Create from dictionary"""
        data['status'] = OrderStatus(data.get('status', 'pending'))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

class SMMPanelAPI:
    """Generic SMM Panel API Client (works with PeakSMM, JAP, GlorySMM)"""

    def __init__(self, name: str, api_url: str, api_key: str, enabled: bool = True):
        self.name = name
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.enabled = enabled
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ZefoyBot/2.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        self._services_cache = None
        self._cache_time = 0

    def _request(self, action: str, params: Dict = None) -> Dict:
        """Make API request"""
        if not self.enabled:
            return {"error": "Panel disabled"}

        try:
            data = {
                "key": self.api_key,
                "action": action,
                **(params or {})
            }

            logger.info(f"[{self.name}] API Request: {action}")

            response = self.session.post(
                f"{self.api_url}",
                data=data,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"[{self.name}] API Response: {result}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"[{self.name}] Request timeout")
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Request error: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            logger.error(f"[{self.name}] Invalid JSON response")
            return {"error": "Invalid response format"}

    def get_balance(self) -> Dict:
        """Get account balance"""
        result = self._request("balance")
        if "balance" in result:
            return {
                "balance": float(result["balance"]),
                "currency": result.get("currency", "USD"),
                "available": True
            }
        return {"balance": 0.0, "currency": "USD", "available": False, "error": result.get("error")}

    def get_services(self, force_refresh: bool = False) -> List[Dict]:
        """Get available services (with caching)"""
        # Cache for 5 minutes
        if not force_refresh and self._services_cache and (time.time() - self._cache_time) < 300:
            return self._services_cache

        result = self._request("services")

        if isinstance(result, list):
            self._services_cache = result
            self._cache_time = time.time()
            return result

        return []

    def find_service(self, service_type: str, platform: str = "tiktok") -> Optional[Dict]:
        """Find service by type and platform"""
        services = self.get_services()

        keywords = {
            "followers": ["followers", "fans", "subscribers"],
            "likes": ["likes", "hearts"],
            "views": ["views", "plays"],
            "shares": ["shares", "reposts"],
            "comments": ["comments", "custom comments"]
        }

        search_terms = keywords.get(service_type, [service_type])

        for service in services:
            name = service.get("name", "").lower()
            category = service.get("category", "").lower()

            # Check if platform matches
            if platform.lower() not in name and platform.lower() not in category:
                continue

            # Check if service type matches
            for term in search_terms:
                if term in name or term in category:
                    return service

        return None

    def place_order(self, service_id: str, url: str, quantity: int, comments: str = None) -> Dict:
        """Place new order"""
        params = {
            "service": service_id,
            "url": url,
            "quantity": quantity
        }

        if comments:
            params["comments"] = comments

        return self._request("add", params)

    def get_order_status(self, order_id: str) -> Dict:
        """Get single order status"""
        return self._request("status", {"order": order_id})

    def get_multiple_orders(self, order_ids: List[str]) -> Dict:
        """Get multiple order statuses (max 100)"""
        if len(order_ids) > 100:
            order_ids = order_ids[:100]

        return self._request("status", {"orders": ",".join(order_ids)})

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        return self._request("cancel", {"order": order_id})

    def refill_order(self, order_id: str) -> Dict:
        """Request refill for order"""
        return self._request("refill", {"order": order_id})

    def get_refill_status(self, refill_id: str) -> Dict:
        """Get refill status"""
        return self._request("refill_status", {"refill": refill_id})

class SMMManager:
    """Main SMM Manager - Handles multiple panels with failover"""

    def __init__(self, config_file: str = "data/smm_config.json"):
        self.config_file = config_file
        self.panels: Dict[str, SMMPanelAPI] = {}
        self.orders_file = "data/smm_orders.json"
        self._load_config()

    def _load_config(self):
        """Load panel configuration"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except:
            # Default configuration
            config = {
                "panels": {
                    "peaksmm": {
                        "name": "PeakSMM",
                        "api_url": "https://www.peaksmm.com/api/v2",
                        "api_key": "YOUR_PEAKSMM_API_KEY",
                        "enabled": False,
                        "priority": 1,
                        "min_balance": 5.0
                    },
                    "justanotherpanel": {
                        "name": "JustAnotherPanel",
                        "api_url": "https://justanotherpanel.com/api/v2",
                        "api_key": "YOUR_JAP_API_KEY",
                        "enabled": False,
                        "priority": 2,
                        "min_balance": 5.0
                    },
                    "glorysmm": {
                        "name": "GlorySMM",
                        "api_url": "https://glorysmmpanel.com/api/v2",
                        "api_key": "YOUR_GLORYSMM_API_KEY",
                        "enabled": False,
                        "priority": 3,
                        "min_balance": 5.0
                    }
                },
                "service_mapping": {
                    "followers": {"search_terms": ["followers", "fans"], "platform": "tiktok"},
                    "likes": {"search_terms": ["likes", "hearts"], "platform": "tiktok"},
                    "views": {"search_terms": ["views", "plays", "video views"], "platform": "tiktok"},
                    "shares": {"search_terms": ["shares", "reposts"], "platform": "tiktok"},
                    "comments": {"search_terms": ["comments", "custom comments"], "platform": "tiktok"}
                }
            }
            self._save_config(config)

        # Initialize panels
        for panel_id, panel_config in config["panels"].items():
            self.panels[panel_id] = SMMPanelAPI(
                name=panel_config["name"],
                api_url=panel_config["api_url"],
                api_key=panel_config["api_key"],
                enabled=panel_config.get("enabled", False)
            )
            self.panels[panel_id].priority = panel_config.get("priority", 99)
            self.panels[panel_id].min_balance = panel_config.get("min_balance", 5.0)

        self.service_mapping = config.get("service_mapping", {})

    def _save_config(self, config: Dict):
        """Save configuration"""
        import os
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_active_panels(self) -> List[Tuple[str, SMMPanelAPI]]:
        """Get list of active panels sorted by priority"""
        active = []
        for panel_id, panel in self.panels.items():
            if panel.enabled:
                active.append((panel_id, panel))

        # Sort by priority
        active.sort(key=lambda x: x[1].priority)
        return active

    def get_best_panel(self, service_type: str) -> Optional[Tuple[str, SMMPanelAPI, Dict]]:
        """Find best panel for service with available balance"""
        mapping = self.service_mapping.get(service_type, {})
        platform = mapping.get("platform", "tiktok")

        for panel_id, panel in self.get_active_panels():
            # Check balance
            balance_info = panel.get_balance()
            if not balance_info["available"]:
                continue
            if balance_info["balance"] < panel.min_balance:
                continue

            # Find service
            service = panel.find_service(service_type, platform)
            if service:
                return (panel_id, panel, service)

        return None

    async def create_order(self, user_id: int, service_type: str, target: str, 
                          quantity: int, comments: str = None) -> SMMOrder:
        """Create and place order on SMM panel"""

        # Generate internal order ID
        internal_id = f"ZFY{int(time.time())}{user_id}"

        # Find best panel
        panel_info = self.get_best_panel(service_type)

        if not panel_info:
            logger.error(f"No panel available for {service_type}")
            return SMMOrder(
                order_id=internal_id,
                external_id=None,
                service=service_type,
                target=target,
                quantity=quantity,
                status=OrderStatus.ERROR,
                price=0.0,
                created_at=time.time(),
                updated_at=time.time(),
                provider="none",
                response_data={"error": "No active panel with sufficient balance"}
            )

        panel_id, panel, service = panel_info
        service_id = str(service["service"])

        # Calculate price
        rate = float(service.get("rate", 0))
        price = (quantity / 1000) * rate

        # Place order
        result = panel.place_order(service_id, target, quantity, comments)

        # Parse response
        if "order" in result:
            external_id = str(result["order"])
            status = OrderStatus.PENDING
            error_msg = None
        else:
            external_id = None
            status = OrderStatus.ERROR
            error_msg = result.get("error", "Unknown error")

        order = SMMOrder(
            order_id=internal_id,
            external_id=external_id,
            service=service_type,
            target=target,
            quantity=quantity,
            status=status,
            price=price,
            created_at=time.time(),
            updated_at=time.time(),
            provider=panel_id,
            charge=0.0,
            start_count=0,
            remains=quantity,
            currency="USD",
            response_data={"place_result": result, "error": error_msg}
        )

        # Save order
        self._save_order(order)

        logger.info(f"Order created: {internal_id} on {panel_id} -> {external_id} ({status.value})")
        return order

    async def update_order_status(self, order: SMMOrder) -> SMMOrder:
        """Check and update order status from panel"""
        if not order.external_id or order.provider not in self.panels:
            return order

        panel = self.panels[order.provider]
        result = panel.get_order_status(order.external_id)

        if "error" in result:
            logger.warning(f"Status check failed for {order.order_id}: {result['error']}")
            return order

        # Update order fields
        order.charge = float(result.get("charge", 0))
        order.start_count = int(result.get("start_count", 0))
        order.remains = int(result.get("remains", 0))
        order.currency = result.get("currency", "USD")
        order.updated_at = time.time()

        # Map status
        panel_status = result.get("status", "").lower()
        status_map = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.PROCESSING,
            "in progress": OrderStatus.IN_PROGRESS,
            "completed": OrderStatus.COMPLETED,
            "complete": OrderStatus.COMPLETED,
            "partial": OrderStatus.PARTIAL,
            "cancelled": OrderStatus.CANCELLED,
            "canceled": OrderStatus.CANCELLED,
            "refunded": OrderStatus.REFUNDED,
            "error": OrderStatus.ERROR,
        }

        new_status = status_map.get(panel_status, order.status)
        if new_status != order.status:
            order.status = new_status
            logger.info(f"Order {order.order_id} status: {new_status.value}")

        order.response_data["last_status"] = result
        self._save_order(order)

        return order

    async def cancel_order(self, order: SMMOrder) -> bool:
        """Cancel an order"""
        if not order.external_id or order.provider not in self.panels:
            return False

        panel = self.panels[order.provider]
        result = panel.cancel_order(order.external_id)

        if "success" in result or "status" in result:
            order.status = OrderStatus.CANCELLED
            order.updated_at = time.time()
            self._save_order(order)
            return True

        return False

    def _save_order(self, order: SMMOrder):
        """Save order to file"""
        try:
            with open(self.orders_file, 'r') as f:
                orders = json.load(f)
        except:
            orders = {}

        orders[order.order_id] = order.to_dict()

        import os
        os.makedirs(os.path.dirname(self.orders_file), exist_ok=True)
        with open(self.orders_file, 'w') as f:
            json.dump(orders, f, indent=2)

    def get_order(self, order_id: str) -> Optional[SMMOrder]:
        """Get order by ID"""
        try:
            with open(self.orders_file, 'r') as f:
                orders = json.load(f)

            if order_id in orders:
                return SMMOrder.from_dict(orders[order_id])
        except:
            pass

        return None

    def get_user_orders(self, user_id: int, limit: int = 10) -> List[SMMOrder]:
        """Get orders for a user"""
        try:
            with open(self.orders_file, 'r') as f:
                orders = json.load(f)

            user_orders = []
            for order_data in orders.values():
                if str(user_id) in order_data["order_id"]:
                    user_orders.append(SMMOrder.from_dict(order_data))

            # Sort by date (newest first)
            user_orders.sort(key=lambda x: x.created_at, reverse=True)
            return user_orders[:limit]
        except:
            return []

    def get_all_panels_status(self) -> Dict:
        """Get status of all panels"""
        status = {}

        for panel_id, panel in self.panels.items():
            balance_info = panel.get_balance()
            services = panel.get_services()

            status[panel_id] = {
                "name": panel.name,
                "enabled": panel.enabled,
                "balance": balance_info.get("balance", 0),
                "currency": balance_info.get("currency", "USD"),
                "available": balance_info.get("available", False),
                "services_count": len(services),
                "status": "active" if balance_info.get("available") and balance_info.get("balance", 0) > 0 else "inactive"
            }

        return status

    def add_panel(self, panel_id: str, name: str, api_url: str, api_key: str, 
                  priority: int = 1, min_balance: float = 5.0):
        """Add new panel dynamically"""
        self.panels[panel_id] = SMMPanelAPI(name, api_url, api_key, enabled=True)
        self.panels[panel_id].priority = priority
        self.panels[panel_id].min_balance = min_balance

        # Save to config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {"panels": {}, "service_mapping": self.service_mapping}

        config["panels"][panel_id] = {
            "name": name,
            "api_url": api_url,
            "api_key": api_key,
            "enabled": True,
            "priority": priority,
            "min_balance": min_balance
        }

        self._save_config(config)

# Integration with main bot
class OrderProcessor:
    """Process orders with real-time updates"""

    def __init__(self, smm_manager: SMMManager):
        self.smm = smm_manager
        self.processing_orders = set()

    async def process_new_order(self, user_id: int, service_type: str, target: str, 
                                 quantity: int) -> SMMOrder:
        """Process new order with real-time updates"""

        # Create order
        order = await self.smm.create_order(user_id, service_type, target, quantity)

        if order.status == OrderStatus.ERROR:
            return order

        # Add to processing
        self.processing_orders.add(order.order_id)

        # Start background monitoring
        asyncio.create_task(self._monitor_order(order))

        return order

    async def _monitor_order(self, order: SMMOrder, max_checks: int = 20):
        """Monitor order status in background"""
        check_intervals = [30, 60, 120, 180, 300]  # Progressive intervals

        for i in range(max_checks):
            # Wait before checking
            wait_time = check_intervals[min(i, len(check_intervals)-1)]
            await asyncio.sleep(wait_time)

            # Update status
            updated = await self.smm.update_order_status(order)

            # Check if completed or failed
            if updated.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, 
                                   OrderStatus.ERROR, OrderStatus.REFUNDED]:
                logger.info(f"Order {order.order_id} finished with status: {updated.status.value}")
                self.processing_orders.discard(order.order_id)
                break

            # Update order object
            order = updated
        else:
            logger.warning(f"Order {order.order_id} max checks reached")
            self.processing_orders.discard(order.order_id)

    async def get_order_progress(self, order: SMMOrder) -> Dict:
        """Get order progress percentage"""
        if order.status == OrderStatus.COMPLETED:
            return {"percent": 100, "status": "completed", "remains": 0}

        if order.status == OrderStatus.ERROR:
            return {"percent": 0, "status": "error", "remains": order.quantity}

        if order.quantity > 0:
            delivered = order.quantity - order.remains
            percent = min(95, int((delivered / order.quantity) * 100))
        else:
            percent = 0

        return {
            "percent": percent,
            "status": order.status.value,
            "remains": order.remains,
            "delivered": order.quantity - order.remains
        }

# Testing
if __name__ == "__main__":
    async def test():
        smm = SMMManager()

        # Check panels
        print("Panel Status:")
        for panel_id, status in smm.get_all_panels_status().items():
            print(f"  {panel_id}: {status}")

        # Test order (if panels configured)
        # order = await smm.create_order(12345, "followers", "https://tiktok.com/@test", 100)
        # print(f"Order: {order}")

    asyncio.run(test())
