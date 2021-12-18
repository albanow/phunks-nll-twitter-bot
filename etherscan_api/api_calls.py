import requests
import json
import time
import secrets_keys as secret


def eth_price_usd(request_try: int, etherscan_eth_prices_url: str):
    '''Get the ethereum price in usd

    Args:
        request_try (int): number of tries for the request
        etherscan_eth_prices_url (str): api url for eth prices

    Returns:
        eht_usd_price (float): ETH prices in USD
    '''
    for _ in range(request_try):
        try:
            # Get the current prices of ETH (BTC/USD)
            eth_prices = requests.post(
                etherscan_eth_prices_url+secret.etherscan_key)
            eth_prices_json = eth_prices.json()
            break
        except (ConnectionResetError, requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            print("ETH prices code error---> ", eth_prices.status_code,
                  "\n", "ETH prices text error---> ", eth_prices.text)
            time.sleep(.1)

     # Extract the ETH price in USD only
    eht_usd_price = float(eth_prices_json["result"]["ethusd"])
    return eht_usd_price


def get_erc721_transfers(request_try: int, url_transfers: str, num_tx: int):
    '''Get the latest transfer(s) from etherscan from an erc721 token contract

    Args:
        request_try (int): number of tries for the request
        url_transfers (str): api url to get the transfers

    Returns:
        eht_usd_price (float): ETH prices in USD
    '''
    headers_req = {'Accept': 'application/json'}

    # URL of the latest transfer in etherscan for a defined contract [ERC-721]
    # you need to have the Token contract number (contract_number) and your etherscan Api-Key Token
    # (etherscan_key) and add them to secrets_keys.py file
    # For reference visit https://etherscan.io/apis
    final_url = url_transfers+secret.contract_number + \
        "&page=1&offset="+str(num_tx)+"&sort=desc&apikey="+secret.etherscan_key
    # Make a request to get the latest transfer(s).
    # Try request_try times in case any exception is throw
    for _ in range(request_try):
        try:
            r_asset = requests.post(final_url, headers=headers_req)
            r_json = r_asset.json()
            r_asset.close()
            break
        except (ConnectionResetError, requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            print("Transfers code error---> ", r_asset.status_code,
                  "\n", "Transfers text error---> ", r_asset.text)
            time.sleep(.1)
    return r_json


def get_last_valid_transfers(
        request_try: int, url_transfers: str, num_tx: int):
    '''Get the latest transfer(s) from etherscan from an erc721 token contract

    Args:
        request_try (int): number of tries for the request
        url_transfers (str): api url to get the transfers

    Returns:
        eht_usd_price (float): ETH prices in USD
    '''
    bid = "0x6d728796"
    sale = "0xf8529df3"
    accepted_bid = "0xbad9f860"
    valid_tx_types = [bid, sale, accepted_bid]
    valid_tx_data = []
    transactions = get_erc721_transfers(
        request_try, url_transfers, num_tx)["result"]
    for tx in transactions:
        input_tx = str(tx["input"])
        tx_type = str(input_tx[0:10])
        if tx_type in valid_tx_types:
            valid_tx_data.append(tx)

    return valid_tx_data
