import time
import secrets_keys as sk
import os
import common.utilities as ut
import etherscan_api.api_calls as etherscan
import twitter_api.api_wrapper as tw

# If you are getting many error response code from the request
# and the bot is failing because of this then please increase this number
request_try = 10
bid_greater_equal = 2
idx = 0
image_name = "nft_image.png"
hash_tags = "#CryptoPhunks #Phunks #NFTs http://notlarvalabs.com"
nll_base_url = "https://NotLarvaLabs.com/CryptoPhunks/Details/"

# All the etherscan related URLs
etherscan_base_url = "https://etherscan.io/tx/"
etherscan_eth_prices = "https://api.etherscan.io/api?module=stats&action=ethprice&apikey="
etherscan_url_transfers = "https://api.etherscan.io/api?module=account&action=txlist&address="
bid = "0x6d728796"
sale = "0xf8529df3"
accepted_bid = "0xbad9f860"

# Seed for the bot to start (latest Txn Hash from Etherscan)
# or you can leave this value empty if you are running the bot for
# the first time
past_tx = ""
latest_tx = ""
time_counter = 0

# Run the Bot til the infinite
while True:

    start = time.time()

    # Make a request to get the latest transfer(s).
    # Try request_try times in case any exception is throw
    transfers = etherscan.get_erc721_transfers(
        request_try, etherscan_url_transfers, 1)

    try:
        # Need to extract the Txn Hash and token of the latest Transfer
        # from etherscan
        Txn_Hash = transfers["result"][idx]["hash"]
        from_address = str(transfers["result"][idx]["from"])
        to_address = str(transfers["result"][idx]["to"])
        input_tx = str(transfers["result"][idx]["input"])
        tx_type = str(input_tx[0:10])
        is_error = str(transfers["result"][idx]["isError"])
    except IndexError:
        # Catch any errors from Etherscan API (response with error)
        print("IndexError: ", transfers)
        end = time.time()
        time_counter = time_counter + (end - start)
        continue

    # Check if the tx was reverted (Fail/error tx) to avoid it
    if is_error == "1":
        end = time.time()
        time_counter = time_counter + (end - start)
        continue
    latest_tx = Txn_Hash

    # Here we check if the current Transaction/Sale is already posted.
    # For this we have captured the previous transaction.
    if latest_tx != past_tx:
        past_tx = latest_tx

        # Get data of the tx type
        tx_type_data = ut.set_tx_type_data(tx_type, input_tx, transfers, idx)
        # If tx is not bid, sale or accepted bid then is an ivalid tx
        if tx_type_data["invalid"]:
            end = time.time()
            time_counter = time_counter + (end - start)
            continue
        # Get needed data from tx
        token_id = tx_type_data["token_id"]
        phunk_url = nll_base_url+token_id
        gwi_value = tx_type_data["gwi_value"]
        action_text = tx_type_data["action_text"]

        if transfers["status"] != "0":
            # Some magic to get all the 'values' and add them to get the real price of
            # the Transfer/Token/NFT in ETH
            asset_price_api = str(gwi_value)

            # Final price(cost) of the Transfer in ETH rounded to 6 decimal
            final_price_eth = ut.convert_to_eth(asset_price_api, 6)
            # Check if tx is a bid then we check if the bid is >= 2eth
            # if not then we avoid the tx
            if tx_type == bid:
                if final_price_eth < bid_greater_equal:
                    end = time.time()
                    time_counter = time_counter + (end - start)
                    continue

            # Current ETH price in USD
            usd_price = etherscan.eth_price_usd(
                request_try, etherscan_eth_prices)
            # Pice in USD of the Token/NFT sale/transfer
            final_price_usd = round(final_price_eth*usd_price, 2)

            # The following only applies if the URL image of your NFT includes
            # the token ID if not then you need to adapt the code to your needs
            # **Contact me if you need help with this
            # For 10,000 NFT collection from 0 to 9999 (2-3 and 4 digits collection)
            token_id = ut.create_token_id_for_image_download(token_id)

            # URL of the NFT image in you server including the NFT token ID
            link_nft_image = "https://phunks.s3.us-east-2.amazonaws.com/images/phunk" + \
                token_id+".png"

            # URL of the 'Transaction Details' (sale/transfer) in etherscan
            # to add it on the twiteer post
            url_tx = etherscan_base_url+Txn_Hash

            # Final text to post in twitter with a custom message, price in ETH,
            # the price in USD, the URL to the Transaction details in etherscan and
            # some hash tags, adapt this code to your needs.
            # **Contact me if you need help with this
            nft_sale_text = ut.create_final_text(
                "Phunk", token_id, action_text, final_price_eth,
                final_price_usd, url_tx, phunk_url, hash_tags)

            # Twitter API connection/authentication
            api = tw.api_authentication()

            # Get all the URLs from the past 15 tweets (post)
            tweets_urls = tw.get_tweets_url_tx(api, sk.twitter_username, 15)

            # If current tx url is in the past 15 posts then we avoid the tweet
            if url_tx in tweets_urls:
                print("Avoiding repetead tweet with tx url: ",  url_tx)
                end = time.time()
                time_counter = time_counter + (end - start)
                continue

            # Create final image wiht purple background for bids and
            # blue background for sales and accepted bids
            ut.create_image_to_post(link_nft_image, image_name, tx_type)

            # Post the message in your Twitter Bot account
            # with the image of the sold NFT attached
            res_status = tw.post_tweet_wiht_media(
                api, image_name, nft_sale_text)

            if "created_at" in res_status._json:
                print("Tweet posted at: ", res_status._json["created_at"])

            # Remove the downloaded image
            os.remove(image_name)
        elif from_address == sk.vault_token_address:
            print(from_address)
    # The Free Api-Key Token from Etherscan only allows Up to 100,000 API calls per day
    # so wait some seconds to make a new request to check for a new Transaction
    # Adapt this wait time as you need
    if time_counter >= 30:
        time_counter = 0

        # Twitter API connection/authentication
        api = tw.api_authentication()

        # Get all the URLs from the past 30 tweets (post)
        last_tweets_urls = tw.get_tweets_url_tx(api, sk.twitter_username, 30)

        # Get last 30 tx
        last_transfers = etherscan.get_last_valid_transfers(
            request_try, etherscan_url_transfers, 30)

        for tx in last_transfers:
            url_tx = etherscan_base_url+tx["hash"]
            if url_tx not in last_tweets_urls:
                tra = {"result": [tx]}
                Txn_Hash = tx["hash"]
                input_tx = str(tx["input"])
                tx_type = str(input_tx[0:10])
                is_error = str(tx["isError"])
                # Get data of the tx type
                tx_type_data = ut.set_tx_type_data(
                    tx_type, input_tx, tra, 0)
                # If tx is not bid, sale or accepted bid then is an ivalid tx
                if tx_type_data["invalid"]:
                    continue
                # Get needed data from tx
                token_id = tx_type_data["token_id"]
                phunk_url = nll_base_url+token_id
                gwi_value = tx_type_data["gwi_value"]
                action_text = tx_type_data["action_text"]

                asset_price_api = str(gwi_value)

                # Final price(cost) of the Transfer in ETH rounded to 6 decimal
                final_price_eth = ut.convert_to_eth(asset_price_api, 6)
                # Check if tx is a bid then we check if the bid is >= 2eth
                # if not then we avoid the tx
                if tx_type == bid:
                    if final_price_eth < bid_greater_equal:
                        continue
                # Current ETH price in USD
                usd_price = etherscan.eth_price_usd(
                    request_try, etherscan_eth_prices)
                # Pice in USD of the Token/NFT sale/transfer
                final_price_usd = round(final_price_eth*usd_price, 2)

                # The following only applies if the URL image of your NFT includes
                # the token ID if not then you need to adapt the code to your needs
                # **Contact me if you need help with this
                # For 10,000 NFT collection from 0 to 9999 (2-3 and 4 digits collection)
                token_id = ut.create_token_id_for_image_download(token_id)

                # URL of the NFT image in you server including the NFT token ID
                link_nft_image = "https://phunks.s3.us-east-2.amazonaws.com/images/phunk" + \
                    token_id+".png"

                # URL of the 'Transaction Details' (sale/transfer) in etherscan
                # to add it on the twiteer post
                url_tx = etherscan_base_url+Txn_Hash

                # Final text to post in twitter with a custom message, price in ETH,
                # the price in USD, the URL to the Transaction details in etherscan and
                # some hash tags, adapt this code to your needs.
                # **Contact me if you need help with this
                nft_sale_text = ut.create_final_text(
                    "Phunk", token_id, action_text, final_price_eth,
                    final_price_usd, url_tx, phunk_url, hash_tags)

                # Create final image wiht purple background for bids and
                # blue background for sales and accepted bids
                ut.create_image_to_post(link_nft_image, image_name, tx_type)

                # Post the message in your Twitter Bot account
                # with the image of the sold NFT attached
                res_status = tw.post_tweet_wiht_media(
                    api, image_name, nft_sale_text)

                if "created_at" in res_status._json:
                    print("Missed Tweet posted at: ",
                          res_status._json["created_at"])

                # Remove the downloaded image
                os.remove(image_name)

    end = time.time()
    time_counter = time_counter + (end - start)
    time.sleep(.1)
