from .gateway import PaymentGateway
from .repository import PaymentRepository


class BillingService:
    def __init__(self, repository: PaymentRepository, gateway: PaymentGateway):
        self.repository = repository
        self.gateway = gateway

    def charge(self, idempotency_key: str, amount: int) -> str:
        existing = self.repository.find_by_key(idempotency_key)
        if existing is not None:
            return existing

        receipt = self.gateway.charge(idempotency_key=idempotency_key, amount=amount)
        self.repository.save(idempotency_key, receipt)
        return receipt
