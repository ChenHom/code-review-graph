class PaymentGateway:
    def __init__(self):
        self._receipts = {}
        self.charge_calls = []

    def charge(self, idempotency_key: str, amount: int) -> str:
        if idempotency_key in self._receipts:
            return self._receipts[idempotency_key]

        receipt = f"receipt-{len(self._receipts) + 1}"
        self._receipts[idempotency_key] = receipt
        self.charge_calls.append((idempotency_key, amount))
        return receipt
