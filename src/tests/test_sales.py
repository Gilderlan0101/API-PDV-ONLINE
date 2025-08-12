import os
import sys

from fastapi import HTTPException
from fastapi.responses import RedirectResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import unittest
from dataclasses import is_dataclass
from src.controllers.sales.sales import Checkout


class TestProduct(unittest.TestCase):

    # Verificando se é uma class
    def test_if_it_is_a_dataclass(self):
        self.assertTrue(is_dataclass(Checkout))

    def setUp(self):
        self.checkout = Checkout(1, 'PROD001', 10, 10.00, 100.00, 'pix')

    # Testando no costrutor da class
    def test_constructor(self):
        self.assertEqual(self.checkout.user_id, 1)
        self.assertEqual(self.checkout.product_name, 'PROD001')
        self.assertEqual(self.checkout.quantity, 10)
        self.assertEqual(self.checkout.total_price, 10.00)
        self.assertEqual(self.checkout.lucro_total, 100.00)
        self.assertEqual(self.checkout.payment_method, 'pix')

    def test_verify_datas_redirect_when_user_id_missing(self):
        checkout = Checkout(None, 'PROD001', 10, 10.00, 100.00, 'pix')  # type: ignore
        result = checkout.verify_datas()
        self.assertIsInstance(result, RedirectResponse)

    def test_verify_datas_raises_when_missing_fields(self):
        checkout = Checkout(1, None, 10, 10.00, 100.00, 'pix')  # type: ignore
        with self.assertRaises(HTTPException) as cm:
            checkout.verify_datas()
        self.assertEqual(cm.exception.status_code, 400)


if __name__ == '__main__':
    unittest.main()
