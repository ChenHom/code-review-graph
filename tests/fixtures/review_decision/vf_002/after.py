class PaymentWorker:
    def __init__(self, billing_service):
        self.billing_service = billing_service

    def handle(self, command, attempt: int = 1) -> str:
        return self.billing_service.charge(
            idempotency_key=f"{command.request_id}:{attempt}",
            amount=command.amount,
        )
