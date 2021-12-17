import requests
import time
import tweepy
import secrets_keys as sk
import os
import json
import utilities as ut

# If you are getting many error response code from the request
# and the bot is failing because of this then please increase this number
request_try = 10
bid_greater_equal = 2
idx = 0
image_name = "nft_image.png"

# Get this from your Twitter development account (not in repo)
# and you need to add them to secrets_keys.py file in your cloned repo
consumer_token = sk.consumer_token
consumer_secret = sk.consumer_secret
key = sk.key
secret = sk.secret

# All the etherscan related URLs
etherscan_base_url = "https://etherscan.io/tx/"
etherscan_eth_prices = "https://api.etherscan.io/api?module=stats&action=ethprice&apikey="
etherscan_url_transfers = "https://api.etherscan.io/api?module=account&action=txlist&address="
bid = "0x6d728796"
sale = "0xf8529df3"
accepted_bid = "0xbad9f860"

# URL of the latest transfer in etherscan for a defined contract [ERC-721]
# you need to have the Token contract number (contract_number) and your etherscan Api-Key Token
# (etherscan_key) and add them to secrets_keys.py file
# For reference visit https://etherscan.io/apis
url_transfers = etherscan_url_transfers+sk.contract_number + \
    "&page=1&offset=1&sort=desc&apikey="+sk.etherscan_key
headers_req = {'Accept': 'application/json'}

# Seed for the bot to start (latest Txn Hash from Etherscan)
# or you can leave this value empty if you are running the bot for
# the first time
past_tx = ""
latest_tx = ""

# Run the Bot til the infinite
while True:

    sum_price = 0
    # Make a request to get the latest transfer.
    # Try request_try times in case any exception is throw
    for _ in range(request_try):
        try:
            r_asset = requests.post(url_transfers, headers=headers_req)
            r_json = r_asset.json()
            r_asset.close()
            break
        except (ConnectionResetError, requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            print("Response code---> ", r_asset.status_code,
                  "\n", "Response text---> ", r_asset.text)
            time.sleep(2)

    try:
        # Need to extract the Txn Hash and token of the latest Transfer
        # from etherscan
        Txn_Hash = r_json["result"][idx]["hash"]
        from_address = str(r_json["result"][idx]["from"])
        to_address = str(r_json["result"][idx]["to"])
        input_tx = str(r_json["result"][idx]["input"])
        tx_type = str(input_tx[0:10])
        is_error = str(r_json["result"][idx]["isError"])
    except IndexError:
        print("IndexError: ", r_json)
        continue

    # Check if the tx was reverted (Fail/error tx)
    if is_error == "1":
        continue
    latest_tx = Txn_Hash

    # Here we check if the current Transaction/Sale is already posted.
    # For this we have captured the previous transaction.
    if latest_tx != past_tx:
        past_tx = latest_tx

        if tx_type == bid:
            token_id = str(ut.get_token_bid_or_sale(input_tx))
            gwi_value = str(r_json["result"][idx]["value"])
            action_text = " has a bid for Ξ"
        elif tx_type == sale:
            token_id = str(ut.get_token_bid_or_sale(input_tx))
            gwi_value = str(r_json["result"][idx]["value"])
            action_text = " was flipped for Ξ"
        elif tx_type == accepted_bid:
            token_value = ut.get_token_accepted_bid(input_tx)
            token_id = str(token_value["token_id"])
            gwi_value = str(token_value["int_value"])
            action_text = " has accepted bid for Ξ"
        else:
            continue

        # There can be multiple transactions for one Transfer, so we iterate in the response
        # to get all the transactions and add all the 'values' in each transaction on the Txn Hash

        if r_json["status"] != "0":
            # Some magic to get all the 'values' and add them to get the real price of
            # the Transfer/Token/NFT in ETH
            asset_price_api = str(gwi_value)

            # Final price(cost) of the Transfer in ETH rounded to 6 decimal
            final_price_eth = ut.convert_to_eth(asset_price_api, 6)
            if tx_type == bid:
                if final_price_eth < bid_greater_equal:
                    continue

            # Make a request to get the ETH current prices (ETH/BTC).
            # Try request_try times in case any exception is throw
            for _ in range(request_try):
                try:
                    # Get the current prices of ETH (BTC/USD)
                    eth_prices = requests.post(
                        etherscan_eth_prices+sk.etherscan_key)
                    eth_prices_json = eth_prices.json()
                    break
                except (ConnectionResetError, requests.exceptions.RequestException, json.decoder.JSONDecodeError):
                    print("Response code---> ", eth_prices.status_code,
                          "\n", "Response text---> ", eth_prices.text)
                    time.sleep(2)

            # Extract the ETH price in USD only
            usd_price = float(eth_prices_json["result"]["ethusd"])
            # Pice in USD of the Token/NFT sale/transfer
            final_price_usd = round(final_price_eth*usd_price, 2)

            # The following only applies if the URL image of your NFT includes
            # the token ID if not then you need to adapt the code to your needs
            # **Contact me if you need help with this
            # For 10,000 NFT collection from 0 to 9999 (4 digits collection)
            if len(token_id) == 1:
                token_id = "00" + token_id
            elif len(token_id) == 2:
                token_id = "0" + token_id

            # URL of the NFT image in you server including the NFT token ID
            link_nft_image = "https://phunks.s3.us-east-2.amazonaws.com/images/phunk" + \
                token_id+".png"

            # URL of the 'Transaction Details' (sale/transfer) in etherscan
            url_tx = etherscan_base_url+Txn_Hash

            # Final text to post in twitter with a custom message, price in ETH,
            # the price in USD, the URL to the Transaction in etherscan and some hash tags,
            # adapt this code to your needs.
            # **Contact me if you need help with this
            nft_sale_text = "Phunk #"+str(token_id) + action_text + \
                str(final_price_eth) + " ($"+str(final_price_usd)+")\n"
            hash_tags = "#CryptoPhunks #Phunks #NFTs http://notlarvalabs.com"
            tweet_text = nft_sale_text + url_tx + "\n" + hash_tags

            # Twitter API connection/authentication
            auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
            try:
                redirect_url = auth.get_authorization_url()
            except tweepy.TweepError:
                print("Error! Failed to get request token.")

            auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
            auth.set_access_token(key, secret)

            api = tweepy.API(auth)
            try:
                api.verify_credentials()
                print("Twitter Authentication Success")
            except:
                print("Twitter Authentication Error")
            tweets_urls = []
            tweets = api.user_timeline(
                screen_name=sk.twitter_username, count=15)
            for tweet in tweets:
                expanded_url = tweet._json["entities"]["urls"][0][
                    "expanded_url"]
                tweets_urls.append(expanded_url)

            if url_tx in tweets_urls:
                print("Avoiding repetead tweet with tx url: ",  url_tx)
                continue

            # Download (temporarily) the NFT image to attach it to the twitter post
            response = requests.get(link_nft_image)
            file = open(image_name, "wb")
            file.write(response.content)
            file.close()
            if tx_type == bid:
                ut.create_background(image_name, (152, 87, 183))
            else:
                ut.create_background(image_name, (96, 131, 151))

            # Post the message in your Twitter Bot account
            # with the image of the sold NFT attached
            media = api.media_upload(image_name)
            # Post the message in your Twitter Bot account
            # with the image of the sold NFT attached
            res_status = api.update_status(
                status=tweet_text, media_ids=[media.media_id])

            if "created_at" in res_status._json:
                print("Tweet posted at: ", res_status._json["created_at"])

            """Remove the downloaded image"""
            os.remove(image_name)
        elif from_address == sk.vault_token_address:
            print(from_address)
    # The Free Api-Key Token from Etherscan only allows Up to 100,000 API calls per day
    # so wait some seconds to make a new request to check for a new Transaction
    # Adapt this wait time as you need
    time.sleep(.5)
