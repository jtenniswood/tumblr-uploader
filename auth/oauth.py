from requests_oauthlib import OAuth1Session

CONSUMER_KEY = "YZ5ScnV9ebDVOV5EOZNavNL8fx4NG0RiFFxuQrzcm7ZM4eQx1P"
CONSUMER_SECRET = "B6063TLTtcPVj1M7C2iEYXihVMyMUyZyfvG4BpeLkeRErVY4LQ"

REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
AUTHORIZE_URL     = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL  = "https://www.tumblr.com/oauth/access_token"

def main():
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
