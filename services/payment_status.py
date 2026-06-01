# Add this at the bottom of services/payment_status.py
import hashlib

from config.config import post_execute_single_payload, get_active_endpoint


def transaction_status_logic(config_data: dict, txnid: str, amount: float, email: str, phone: str) -> tuple:
    endpoint_url = get_active_endpoint('status', "")

    payload = {
        "key": config_data.get("key"),
        "txnid": txnid,
        "amount": f"{amount:.2f}",
        "email": email,
        "phone": phone
    }

    hash_sequence = (
        f"{payload['key']}|{payload['txnid']}|{payload['amount']}|"
        f"{payload['email']}|{payload['phone']}|{config_data.get('salt')}"
    )
    payload["hash"] = hashlib.sha512(hash_sequence.encode('utf-8')).hexdigest().lower()

    response = post_execute_single_payload(endpoint_url, payload)

    return payload, endpoint_url, response