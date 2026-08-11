from dataclasses import dataclass

from .billing_service import BillingService


@dataclass(frozen=True)
class PaymentCommand:
    request_id: str
    amount: int


class PaymentWorker:
    def __init__(self, billing_service: BillingService):
        self.billing_service = billing_service

    def handle(self, command: PaymentCommand, attempt: int = 1) -> str:
        return self.billing_service.charge(
            idempotency_key=f"{command.request_id}:{attempt}",
            amount=command.amount,
        )
