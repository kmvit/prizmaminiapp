import decimal
import hashlib
from urllib import parse
from urllib.parse import urlparse


class RobokassaService:
    def __init__(self, merchant_login: str, merchant_password_1: str, merchant_password_2: str):
        self.merchant_login = merchant_login
        self.merchant_password_1 = merchant_password_1
        self.merchant_password_2 = merchant_password_2

    def calculate_signature(self, *args) -> str:
        """Create signature MD5.
        """
        return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()

    def parse_response(self, request: str) -> dict:
        """
        :param request: Link.
        :return: Dictionary.
        """
        params = {}

        for item in urlparse(request).query.split('&'):
            key, value = item.split('=')
            params[key] = value
        return params

    def check_signature_result(
        self,
        order_number: int,  # invoice number
        received_sum: decimal,  # cost of goods, RU
        received_signature: hex,  # SignatureValue
        password: str  # Merchant password
    ) -> bool:
        signature = self.calculate_signature(received_sum, order_number, password)
        if signature.lower() == received_signature.lower():
            return True
        return False

    def generate_payment_link(
        self,
        cost: decimal,  # Cost of goods, RU
        number: int,  # Invoice number
        description: str,  # Description of the purchase
        is_test = 0,
        robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx',
    ) -> str:
        """URL for redirection of the customer to the service.
        """
        signature = self.calculate_signature(
            self.merchant_login,
            cost,
            number,
            self.merchant_password_1
        )

        data = {
            'MerchantLogin': self.merchant_login,
            'OutSum': cost,
            'InvId': number,
            'Description': description,
            'SignatureValue': signature,
            'IsTest': is_test
        }
        return f'{robokassa_payment_url}?{parse.urlencode(data)}'

    def result_payment(self, request: str) -> str:
        """Verification of notification (ResultURL).
        :param request: HTTP parameters.
        """
        param_request = self.parse_response(request)
        cost = param_request['OutSum']
        number = param_request['InvId']
        signature = param_request['SignatureValue']


        if self.check_signature_result(number, cost, signature, self.merchant_password_2):
            return f'OK{param_request["InvId"]}'
        return "bad sign"

    def check_success_payment(self, request: str) -> str:
        """ Verification of operation parameters ("cashier check") in SuccessURL script.
        :param request: HTTP parameters
        """
        param_request = self.parse_response(request)
        cost = param_request['OutSum']
        number = param_request['InvId']
        signature = param_request['SignatureValue']


        if self.check_signature_result(number, cost, signature, self.merchant_password_1):
            return "Thank you for using our service"
        return "bad sign" 