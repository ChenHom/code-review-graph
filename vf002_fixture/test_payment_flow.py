import unittest

from .billing_service import BillingService
from .gateway import PaymentGateway
from .repository import PaymentRepository
from .worker import PaymentCommand, PaymentWorker


class PaymentFlowTest(unittest.TestCase):
    def setUp(self):
        self.gateway = PaymentGateway()
        self.repository = PaymentRepository()
        self.service = BillingService(self.repository, self.gateway)
        self.worker = PaymentWorker(self.service)

    def test_service_reuses_existing_charge_for_same_key(self):
        first = self.service.charge("req-100", 500)
        second = self.service.charge("req-100", 500)

        self.assertEqual(first, second)
        self.assertEqual(1, len(self.gateway.charge_calls))

    def test_worker_processes_payment(self):
        receipt = self.worker.handle(PaymentCommand("req-200", 800))

        self.assertEqual("receipt-1", receipt)
        self.assertEqual([("req-200", 800)], self.gateway.charge_calls)


if __name__ == "__main__":
    unittest.main()
