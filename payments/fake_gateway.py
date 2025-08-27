import random
import time
from decimal import Decimal
from typing import Dict, Any
import uuid

class FakePaymentGateway:
    """
    Fake payment gateway that simulates Payme/Click behavior
    """
    
    def __init__(self):
        self.success_rate = 0.85  # 85% success rate
    
    def process_payment(self, amount: Decimal, payment_method: str, card_data: Dict = None) -> Dict[str, Any]:
        """
        Simulate payment processing
        """
        time.sleep(random.uniform(1, 3))
        
        transaction_id = str(uuid.uuid4())
        is_successful = random.random() < self.success_rate
        
        if is_successful:
            return {
                'status': 'success',
                'transaction_id': transaction_id,
                'gateway_response': {
                    'code': '200',
                    'message': 'Payment processed successfully',
                    'amount': str(amount),
                    'currency': 'USD',
                    'payment_method': payment_method,
                    'timestamp': int(time.time()),
                    'gateway_fee': str(Decimal(str(amount)) * Decimal('0.03')),  # 3% fee
                }
            }
        else:
            error_codes = {
                'INSUFFICIENT_FUNDS': 'Insufficient funds',
                'CARD_DECLINED': 'Card declined by issuer',
                'INVALID_CARD': 'Invalid card details',
                'NETWORK_ERROR': 'Network timeout',
                'FRAUD_DETECTED': 'Transaction flagged as potentially fraudulent'
            }
            
            error_code = random.choice(list(error_codes.keys()))
            
            return {
                'status': 'failed',
                'transaction_id': transaction_id,
                'error_code': error_code,
                'error_message': error_codes[error_code],
                'gateway_response': {
                    'code': '400',
                    'message': error_codes[error_code],
                    'amount': str(amount),
                    'currency': 'USD',
                    'payment_method': payment_method,
                    'timestamp': int(time.time()),
                }
            }
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Simulate payment verification
        """
        return {
            'status': 'completed',
            'transaction_id': transaction_id,
            'verified': True,
            'timestamp': int(time.time())
        }
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """
        Simulate payment refund
        """
        time.sleep(random.uniform(0.5, 1.5))
        
        return {
            'status': 'refunded',
            'refund_id': str(uuid.uuid4()),
            'original_transaction_id': transaction_id,
            'refunded_amount': str(amount) if amount else 'full',
            'timestamp': int(time.time())
        }

payme_gateway = FakePaymentGateway()
click_gateway = FakePaymentGateway()
card_gateway = FakePaymentGateway()

GATEWAY_MAP = {
    'payme': payme_gateway,
    'click': click_gateway,
    'card': card_gateway,
}