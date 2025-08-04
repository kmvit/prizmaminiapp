import decimal
import hashlib

from urllib.parse import urlparse, urlencode


class RobokassaService:
    def __init__(self, merchant_login: str, merchant_password_1: str, merchant_password_2: str, is_test: int):
        self.merchant_login = merchant_login
        self.merchant_password_1 = merchant_password_1
        self.merchant_password_2 = merchant_password_2
        self.is_test = is_test

    def calculate_signature(self, *args) -> str:
        """Create signature MD5."""
        return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()

    def parse_response(self, request: str) -> dict:
        params = {}
        for item in urlparse(request).query.split('&'):
            key, value = item.split('=')
            params[key] = value
        return params

    def check_signature_success(self, out_sum, inv_id, received_signature):
        # OutSum обязательно строка с двумя знаками после запятой!
        out_sum_str = "{:.2f}".format(float(out_sum)) if not isinstance(out_sum, str) else out_sum
        signature = self.calculate_signature(out_sum_str, inv_id, self.merchant_password_1)
        return signature.lower() == received_signature.lower()

    def check_signature_result(self, out_sum, inv_id, received_signature):
        # OutSum обязательно строка с двумя знаками после запятой!
        out_sum_str = "{:.2f}".format(float(out_sum)) if not isinstance(out_sum, str) else out_sum
        signature = self.calculate_signature(out_sum_str, inv_id, self.merchant_password_2)
        print(f"[Robokassa] Проверка подписи ResultURL:")
        print(f"[Robokassa] out_sum_str: {out_sum_str}")
        print(f"[Robokassa] inv_id: {inv_id}")
        print(f"[Robokassa] received_signature: {received_signature}")
        print(f"[Robokassa] calculated_signature: {signature}")
        print(f"[Robokassa] password2: {self.merchant_password_2}")
        result = signature.lower() == received_signature.lower()
        print(f"[Robokassa] Подписи совпадают: {result}")
        return result

    def generate_payment_link(
        self,
        cost: decimal,  # Cost of goods, RU
        number: int,  # Invoice number
        description: str,  # Description of the purchase
        is_test: int,
        success_url: str = None,  # URL для успешного платежа
        fail_url: str = None,     # URL для неуспешного платежа
        robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx',
    ) -> str:
        # Форматируем сумму с двумя знаками после запятой
        out_sum = "{:.2f}".format(float(cost))
        
        # Создаем подпись для платежа
        signature = self.calculate_signature(
            self.merchant_login,
            out_sum,
            number,
            self.merchant_password_1
        )
        data = {
            'MerchantLogin': self.merchant_login,
            'OutSum': out_sum,
            'InvId': number,
            'Description': description,
            'SignatureValue': signature,
            'IsTest': is_test
        }
        if success_url:
            data['SuccessURL'] = success_url
        if fail_url:
            data['FailURL'] = fail_url
        link = f'{robokassa_payment_url}?{urlencode(data)}'
        print("[Robokassa] MerchantLogin:", self.merchant_login)
        print("[Robokassa] OutSum:", out_sum)
        print("[Robokassa] InvId:", number)
        print("[Robokassa] Description:", description)
        print("[Robokassa] SignatureValue:", signature)
        print("[Robokassa] IsTest:", is_test)
        print("[Robokassa] SuccessURL:", success_url)
        print("[Robokassa] FailURL:", fail_url)
        print("[Robokassa] Password1:", self.merchant_password_1)
        print("[Robokassa] Итоговая ссылка:", link)
        print("[Robokassa] Проверка подписи SuccessURL:")
        test_signature = self.calculate_signature(out_sum, number, self.merchant_password_1)
        print(f"[Robokassa] Ожидаемая подпись SuccessURL: {test_signature}")
        print(f"[Robokassa] Проверка подписи ResultURL:")
        test_signature_result = self.calculate_signature(out_sum, number, self.merchant_password_2)
        print(f"[Robokassa] Ожидаемая подпись ResultURL: {test_signature_result}")
        return link 