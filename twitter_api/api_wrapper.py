import tweepy


def api_authentication(
        consumer_token: str, consumer_secret: str, key: str, secret: str):
    '''Connection to the twitter API

    Args:
        consumer_token (str): Consumer Keys (API Key)
        consumer_secret (str): Consumer Keys (API Secret Key)
        key (str): Authentication Tokens (Access Token)
        secret (str): Authentication Tokens (Access Token Secret)

    Returns:
        api: api connection
    '''
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
    except:
        print("Twitter Authentication Error")

    return api


def get_tweets_url_tx(api, twitter_username: str, num_tweets: int):
    '''Get the tx URLs from the last tweets 

    Args:
        api : twitter api object
        twitter_username (str): Twitter username to get the urls
        num_tweets (str): Number of tweets to get the urls

    Returns:
        tweets_urls (list): a list with the tx urls
    '''
    tweets = api.user_timeline(
        screen_name=twitter_username, count=num_tweets)

    tweets_urls = []
    for tweet in tweets:
        expanded_url = tweet._json["entities"]["urls"][0][
            "expanded_url"]
        tweets_urls.append(expanded_url)
    return tweets_urls


def post_tweet_wiht_media(api, image_path: str, tweet_text: str):
    '''Post a tweet wiht media attached to it (image)

    Args:
        api : twitter api object
        image_path (str): Path to the image to attach
        tweet_text (str): Text to attach to the twwet

    Returns:
        res_status (json): status of the tweet posted
    '''
    # Post the message in your Twitter Bot account
    # with the image of the sold NFT attached
    media = api.media_upload(image_path)
    res_status = api.update_status(
        status=tweet_text, media_ids=[media.media_id])

    return res_status
