# Basic Setup

### Check that Python3 is installed
python3 --version

### Install Python3
sudo apt-get update
sudo apt-get install python3

### Install pip
sudo apt-get install python3-pip




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




# Upload

### Install pytumblr
sudo pip3 install pytumblr

### Setup script
sudo nano upload.py

### Run the script
python3 upload.py
