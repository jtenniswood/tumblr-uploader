import os
from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
AUTHORIZE_URL     = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL  = "https://www.tumblr.com/oauth/access_token"

def main():
    # Retrieve consumer key and secret from environment variables
    CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")

    if not CONSUMER_KEY or not CONSUMER_SECRET:
        raise ValueError("Environment variables CONSUMER_KEY and CONSUMER_SECRET must be set.")

    # 1. New request token
    oauth = OAuth1Session(client_key=CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    request_token_data = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    resource_owner_key = request_token_data["oauth_token"]
    resource_owner_secret = request_token_data["oauth_token_secret"]

    # 2. Authorization URL
    auth_url = oauth.authorization_url(AUTHORIZE_URL)
    print("Open this URL in your browser and authorize the app:\n", auth_url)

    # 3. Tumblr gives a verifier code
    verifier = input("Paste the verifier code here: ").strip()

    # 4. Exchange for access token
    oauth = OAuth1Session(
        client_key=CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    print("Your OAuth Token:", tokens["oauth_token"])
    print("Your OAuth Token Secret:", tokens["oauth_token_secret"])

if __name__ == "__main__":
    main()
