from config.config import generate_txnid, generate_hash, get_active_endpoint, post_execute_single_payload


def initiate_payment_logic(config_data: dict, base_payload: dict, extra_args: dict = None) -> tuple:
    """
    Core logic for initiating a payment.
    Returns: (transaction_id, final_payload, api_response_dict)
    """
    txnid = generate_txnid()
    endpoint_url = get_active_endpoint('initiate', "")

    # 1. Assemble Payload
    payload = {
        "key": config_data.get("key"),
        "txnid": txnid,
        "surl": "https://localhost/success",
        "furl": "https://localhost/failure",
        **base_payload
    }

    if extra_args:
        payload.update(extra_args)

    # 2. Hash and Execute
    payload["hash"] = generate_hash(payload, config_data.get("salt"))
    response = post_execute_single_payload(endpoint_url, payload)

    return txnid, payload, endpoint_url, response


def seamless_payment_logic(config_data: dict, access_key: str, mode: str, instrument_details: dict) -> tuple:
    """
    Core logic for executing the Step-2 Seamless Payment push.
    Returns: (final_payload, endpoint_url, api_response_dict)
    """
    endpoint_url = get_active_endpoint('seamless', "")

    # 1. Assemble Payload (Access Key + Instrument Details)
    payload = {
        "access_key": access_key,
        "payment_mode": mode,
        **instrument_details
    }

    # 2. Execute Request (No hash required for Step 2 seamless capture)
    response = post_execute_single_payload(endpoint_url, payload)

    return payload, endpoint_url, response