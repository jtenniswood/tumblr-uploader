

# Authorize

### Install oauth
pip install requests requests-oauthlib

### Setup auth script
sudo nano oauth.py 

### Run the script
python3 oauth.py

### Paste response
*Copy the verifier part of the URL, removing the final #=*
http://localhost:8080/?oauth_token=XXXXXX&oauth_verifier=YYYYYY

*Then copy the oauth key and secrets, you’ll need this for pytumblr to work*
