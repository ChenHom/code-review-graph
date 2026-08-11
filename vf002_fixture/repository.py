class PaymentRepository:
    def __init__(self):
        self._receipts = {}

    def find_by_key(self, idempotency_key: str):
        return self._receipts.get(idempotency_key)

    def save(self, idempotency_key: str, receipt: str) -> None:
        self._receipts[idempotency_key] = receipt
