

# Authorize

### Install pip
sudo apt install python3-pip

### Install oauth
pip install requests requests-oauthlib

### Run the script
python3 oauth.py

### Paste response
*Copy the verifier part of the URL, removing the final #=*
http://localhost:8080/?oauth_token=XXXXXX&oauth_verifier=YYYYYY

*Then copy the oauth key and secrets, you’ll need this for pytumblr to work*



# Publishing

#### Build
sudo docker build -t tumblr-uploader .

#### Sign in to Docker
sudo docker login

#### Add container tag
sudo docker tag tumblr-uploader jtenniswood/tumblr-uploader:latest

#### Upload container
sudo docker push jtenniswood/tumblr-uploader:latest
