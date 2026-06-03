PAYMENT_INITIATE_SCHEMA = {
    "udf1": {"label": "User Defined Field 1", "type": str},
    "udf2": {"label": "User Defined Field 2", "type": str},
    "udf3": {"label": "User Defined Field 3", "type": str},
    "udf4": {"label": "User Defined Field 4", "type": str},
    "udf5": {"label": "User Defined Field 5", "type": str},
    "udf6": {"label": "User Defined Field 6", "type": str},
    "udf7": {"label": "User Defined Field 7", "type": str},
    "address1": {"label": "Billing Address Line 1", "type": str},
    "address2": {"label": "Billing Address Line 2", "type": str},
    "city": {"label": "City", "type": str},
    "state": {"label": "State", "type": str},
    "country": {"label": "Country", "type": str},
    "zipcode": {"label": "Zip/Postal Code (Max 6 digits)", "type": str},
    "show_payment_mode": {"label": "Show Payment Mode (e.g., NB,CC,DC)", "type": str},
    "split_payments": {"label": "Split Payments Array (Valid JSON string)", "type": str},
    "request_flow": {"label": "Request Flow", "type": str},
    "sub_merchant_id": {"label": "Sub Merchant ID", "type": str},
    "payment_category": {"label": "Payment Category", "type": str},
    "account_no": {"label": "Account Number", "type": str},
    "ifsc": {"label": "IFSC Code", "type": str},
    "unique_id": {"label": "Unique Identifier", "type": str}
}

SEAMLESS_INSTRUMENT_SCHEMA = {
    "CC": {
        "card_number": {"label": "Card Number", "type": str},
        "card_holder_name": {"label": "Name on Card", "type": str},
        "card_cvv": {"label": "CVV (Secret)", "type": str},
        "card_expiry_date": {"label": "Expiry Date (MM/YYYY)", "type": str}
    },
    "DC": {
        "card_number": {"label": "Card Number", "type": str},
        "card_holder_name": {"label": "Name on Card", "type": str},
        "card_cvv": {"label": "CVV (Secret)", "type": str},
        "card_expiry_date": {"label": "Expiry Date (MM/YYYY)", "type": str}
    },
    "NB": {
        "bank_code": {"label": "Bank Code (e.g., HDFB)", "type": str}
    },
    "MW": {
        "bank_code": {"label": "Wallet Code (e.g., PAYTM)", "type": str}
    },
    "UPI": {
        "upi_va": {"label": "UPI VPA (e.g., test@upi) [Leave blank if using QR]", "type": str},
        "upi_qr": {"label": "Generate UPI Deep Link / QR?", "type": bool}
    },
    "PL": {
        "pay_later_app": {"label": "Pay Later App (e.g., Simpl)", "type": str}
    },
    "EMI": {
        "card_number": {"label": "Card Number", "type": str},
        "card_holder_name": {"label": "Name on Card", "type": str},
        "card_cvv": {"label": "CVV (Secret)", "type": str},
        "card_expiry_date": {"label": "Expiry Date (MM/YYYY)", "type": str},
        "emi_object": {"label": "EMI Object (Valid JSON string)", "type": str}
    }
}

