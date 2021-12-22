from PIL import Image
import requests
import os

bid = "0x6d728796"
sale = "0xf8529df3"
accepted_bid = "0xbad9f860"


def create_background(image_path: str, rgb_color):
    '''Add custom background to transparent bg png image

    Args:
        image_path (str): Path to the image to add the bg
        rgb_color (tuple): tuple with the rgb color for the bg
    '''
    image = Image.open(image_path).convert('RGBA')

    color = Image.new(mode="RGBA", size=image.size, color=rgb_color)
    color.save("color.png", format="png")

    background = Image.open("color.png").convert("RGBA")
    comp1 = Image.alpha_composite(background, image)

    rgb_im = comp1.convert('RGB')
    rgb_im.save(image_path, format="png")
    os.remove("color.png")


def get_token_bid_or_sale(hex_input: str):
    '''Get the token id from hex input (bid or sale tx)

    Args:
        hex_input (str): the input from tx in hex format

    Returns:
        int_token (int): token ID
    '''
    hex_token = hex_input[-64:]
    int_token = int(hex_token, 16)

    return int_token


def get_token_accepted_bid(hex_input: str):
    '''Get the token id from hex input (accepted bid tx)

    Args:
        hex_input (str): the input from tx in hex format

    Returns:
        int_token (int): token ID
    '''
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
    '''Covert gwi to eth values

    Args:
        value (str): eth value in gwi
        decimals (int): decimals to round eth value

    Returns:
        final_price_eth (float): value of gwi in eth
    '''
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


def set_tx_type_data(tx_type: str, input_tx: str, transfers, idx: int):
    '''Covert gwi to eth values

    Args:
        tx_type (str): tx type to get data
        input_tx (str): input from tx in hex format
        transfers (json): transfer(s)
        idx (int): idx to get the data

    Returns:
        tx_data (json): set data for the tx type
    '''
    # Checking the tx type to create the correct tweet text
    tx_data = {"invalid": False}
    if tx_type == bid:
        tx_data["token_id"] = str(get_token_bid_or_sale(input_tx))
        tx_data["gwi_value"] = str(transfers["result"][idx]["value"])
        tx_data["action_text"] = " has a bid for Ξ"
    elif tx_type == sale:
        tx_data["token_id"] = str(get_token_bid_or_sale(input_tx))
        tx_data["gwi_value"] = str(transfers["result"][idx]["value"])
        tx_data["action_text"] = " was flipped for Ξ"
    elif tx_type == accepted_bid:
        token_value = get_token_accepted_bid(input_tx)
        tx_data["token_id"] = str(token_value["token_id"])
        tx_data["gwi_value"] = str(token_value["int_value"])
        tx_data["action_text"] = " has accepted bid for Ξ"
    else:
        tx_data["invalid"] = True

    return tx_data


def download_image(image_url: str, image_name: str):
    '''Download image from URL

    Args:
        image_url (str): url of the image to download
        image_name (str): image name to save it in root
    '''
    response = requests.get(image_url)
    file = open(image_name, "wb")
    file.write(response.content)
    file.close()


def create_final_image(tx_type: str, image_name: str):
    '''Download image from URL

    Args:
        tx_type (str): tx type to create the image
        image_name (str): image name to save it in root
    '''
    if tx_type == bid:
        create_background(image_name, (152, 87, 183))
    else:
        create_background(image_name, (96, 131, 151))


def create_image_to_post(image_url: str, image_name: str, tx_type: str):
    '''Create the image to post on twitter

    Args:
        image_url (str): url of the image to download
        image_name (str): image name to save it in root
        tx_type (str): tx type to create the image
    '''
    download_image(image_url, image_name)
    create_final_image(tx_type, image_name)


def create_final_text(
        project_name: str, token_id: str, action_text: str, final_price_eth,
        final_price_usd, url_tx, url_nft, hash_tags):
    '''Create the image to post on twitter

    Args:
        project_name (str): Project name to append at the start of the text
        token_id (str): token id of the NFT
        action_text (str): action text to append to the final text
        final_price_eth : final price of the tx (in eth)
        final_price_usd : final price of the tx (in usd)
        url_tx (str): url of the transaction
        url_nft (str): url of the NFT sale on the marketplace
        hash_tags (str): some hashtags to add to the tweet

        Returns:
        tweet_text (str): final text to tweet
    '''
    nft_sale_text = project_name+" #"+str(token_id) + action_text + \
        str(final_price_eth) + " ($"+str(final_price_usd)+")\n"
    tweet_text = nft_sale_text + u"\U0001F4CA" + url_nft + "\n" + u"\U0001F50D"+url_tx + "\n" + hash_tags

    return tweet_text


def create_token_id_for_image_download(token_id):
    '''Create the image to post on twitter

    Args:
        token_id (str): token id of the NFT

    Returns:
        token_id_res (str): token id to downlad image
    '''
    token_id_res = token_id
    if len(token_id) == 1:
        token_id_res = "00" + token_id
    elif len(token_id) == 2:
        token_id_res = "0" + token_id

    return token_id_res
