PAYMENT_INITIATE_SCHEMA = {
    # Mandatory fields that the user MUST provide
    "mandatory": {
        "amount": "Payment Amount (e.g., 50.00)",
        "firstname": "Customer First Name",
        "email": "Customer Email ID",
        "phone": "Customer Mobile Number",
        "productinfo": "Product Info/Description"
    },

    # Optional fields the user CAN provide or omit
    "optional": {
        "udf1": "User Defined Field 1",
        "udf2": "User Defined Field 2",
        "udf3": "User Defined Field 3",
        "udf4": "User Defined Field 4",
        "udf5": "User Defined Field 5",
        "udf6": "User Defined Field 6",
        "udf7": "User Defined Field 7",
        "address1": "Billing Address Line 1",
        "address2": "Billing Address Line 2",
        "city": "City",
        "state": "State",
        "country": "Country",
        "zipcode": "Zip/Postal Code",
        "show_payment_mode": "Show Payment Mode",
        "split_payments": "Split Payments Array",
        "request_flow": "Request Flow",
        "sub_merchant_id": "Sub Merchant ID",
        "payment_category": "Payment Category",
        "account_no": "Account Number",
        "ifsc": "IFSC Code",
        "unique_id": "Unique Identifier"
    }
}

SEAMLESS_INSTRUMENT_SCHEMA = {
    "CC": {
        "card_number": "Card Number",
        "card_holder_name": "Name on Card",
        "card_cvv": "CVV (Secret)",
        "card_expiry_date": "Expiry Date (MM/YYYY)"
    },
    "DC": {
        "card_number": "Card Number",
        "card_holder_name": "Name on Card",
        "card_cvv": "CVV (Secret)",
        "card_expiry_date": "Expiry Date (MM/YYYY)"
    },
    "NB": {
        "bank_code": "Bank Code (e.g., HDFB)"
    },
    "MW": {
        "bank_code": "Wallet Code (e.g., PAYTM)"
    },
    "UPI": {
        "upi_va": "UPI VPA (e.g., test@upi)"
    },
    "PL": {
        "pay_later_app": "Pay Later App (e.g., Simpl)"
    },
    "EMI": {
        "card_number": "Card Number",
        "card_holder_name": "Name on Card",
        "card_cvv": "CVV (Secret)",
        "card_expiry_date": "Expiry Date (MM/YYYY)",
        "emi_object": "EMI Object (JSON string)"
    }
}

