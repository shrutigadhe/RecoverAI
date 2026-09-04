import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
import razorpay
from app.config import settings

logger = logging.getLogger("recoverai.razorpay_service")


class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.demo_mode = settings.DEMO_MODE

        # Initialize official Razorpay SDK client if keys are real
        self.client = None
        if self.key_id and self.key_secret and not self.key_id.startswith("rzp_test_mock"):
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as e:
                logger.warning(f"Failed to initialize Razorpay SDK client: {e}")

    def create_order(self, amount: float, currency: str = "INR", receipt: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates an order. Converts amount to smallest currency unit (paise for INR).
        """
        amount_in_paise = int(amount * 100)

        if self.client and not self.demo_mode:
            try:
                order_data = {
                    "amount": amount_in_paise,
                    "currency": currency,
                    "receipt": receipt or "receipt_1",
                    "payment_capture": 1
                }
                rzp_order = self.client.order.create(data=order_data)
                rzp_order["is_demo"] = False
                return rzp_order
            except Exception as e:
                logger.error(f"Razorpay API error creating order: {e}")
                # Fall back to simulated demo order if API fails
                pass

        # Demo mode / Fallback order
        return {
            "id": f"order_demo_{hashlib.md5(str(amount).encode()).hexdigest()[:10]}",
            "entity": "order",
            "amount": amount_in_paise,
            "amount_paid": 0,
            "amount_due": amount_in_paise,
            "currency": currency,
            "receipt": receipt or "receipt_demo",
            "status": "created",
            "attempts": 0,
            "notes": {"mode": "DEMO_SIMULATED"},
            "created_at": 1690000000,
            "is_demo": True
        }

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches payment status from Razorpay or simulates response.
        """
        if self.client and not self.demo_mode and not payment_id.startswith("pay_demo_"):
            try:
                payment_data = self.client.payment.fetch(payment_id)
                payment_data["is_demo"] = False
                return payment_data
            except Exception as e:
                logger.error(f"Error fetching Razorpay payment {payment_id}: {e}")

        # Simulated response
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 350000,
            "currency": "INR",
            "status": "captured" if "success" in payment_id else "failed",
            "order_id": "order_demo_123",
            "method": "upi",
            "error_code": "BAD_REQUEST_ERROR" if "failed" in payment_id else None,
            "error_description": "Bank servers unavailable" if "failed" in payment_id else None,
            "is_demo": True
        }

    def verify_webhook_signature(self, payload_body: bytes, signature: str) -> bool:
        """
        Verifies Razorpay HMAC SHA256 webhook signature.
        In DEMO_MODE with mock secrets, returns True if signature is 'demo_signature' or mock.
        """
        if self.demo_mode and (signature == "demo_signature" or self.webhook_secret == "mock_webhook_secret"):
            return True

        if not self.webhook_secret:
            logger.warning("No webhook secret configured")
            return False

        try:
            expected_signature = hmac.new(
                key=self.webhook_secret.encode('utf-8'),
                msg=payload_body,
                digestmod=hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def retry_payment(self, razorpay_order_id: str, amount: float) -> Dict[str, Any]:
        """
        Executes bounded retry payment simulation/call.
        """
        if self.client and not self.demo_mode:
            # Razorpay API doesn't allow direct re-charge without customer authorization link or payment link;
            # For Test Mode orders, create a payment link or new retry order.
            try:
                link = self.client.payment_link.create({
                    "amount": int(amount * 100),
                    "currency": "INR",
                    "accept_partial": False,
                    "description": f"Retry payment for order {razorpay_order_id}",
                    "reminder_enable": True
                })
                return {
                    "success": True,
                    "status": "authorized_link_created",
                    "payment_link": link.get("short_url"),
                    "is_demo": False
                }
            except Exception as e:
                logger.error(f"Razorpay retry payment link creation failed: {e}")

        # Simulated retry outcome
        return {
            "success": True,
            "status": "captured",
            "amount": amount,
            "razorpay_payment_id": f"pay_retry_{hashlib.md5(str(amount).encode()).hexdigest()[:8]}",
            "message": "Payment retry successfully captured in test mode",
            "is_demo": True
        }
