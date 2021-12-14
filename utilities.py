def get_token_bid_or_sale(hex_input: str):
    hex_token = hex_input[-64:]
    int_token = int(hex_token, 16)
    return int_token


def get_token_accepted_bid(hex_input: str):
    hex_token = hex_input[11:74]
    int_token = int(hex_token, 16)
    hex_value = hex_input[-64:]
    int_value = int(hex_value, 16)

    data = {
        "token_id": int_token,
        "int_value": int_value
    }
    return data


def convert_to_eth(value: str, decimals: int):
    price_size = len(value)
    asset_dec_int = 18

    if price_size < asset_dec_int:
        diff = asset_dec_int - price_size
        for n in range(diff):
            value = '0' + value

        value = "."+value

        for idx, val in enumerate(reversed(value)):
            if val != "0":
                if idx == 0:
                    asset_price = value
                else:
                    asset_price = value[:-idx]
                break
    else:
        asset_price = round(
            float(
                value[: price_size - asset_dec_int] + "." +
                value[price_size - asset_dec_int:]),
            6)

    # Final price(cost) of the Transfer in ETH rounded to decimals
    final_price_eth = round(float(asset_price), decimals)

    return final_price_eth
