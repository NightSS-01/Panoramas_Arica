"""Conexión con Webpay Plus (ambiente de integración, solo pruebas)."""
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.webpay.webpay_plus.transaction import Transaction


def _transaccion():
    return Transaction.build_for_integration(
        IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY
    )


def crear(buy_order, session_id, monto, return_url):
    """Devuelve un diccionario con 'token' y 'url'."""
    return _transaccion().create(buy_order, session_id, monto, return_url)


def confirmar(token):
    """Devuelve un diccionario con el resultado final del pago."""
    return _transaccion().commit(token)