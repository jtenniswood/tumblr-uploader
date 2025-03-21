# Tumblr Uploader
This is an uploader for Tumblr, it monitors category based folder, uploads them (with options for using the draft, queue or direct publishing). If there is an issue, it will move it to the failed folder, if it succeeds it will just delete the original file.


## Authorize

#### Register an application
`https://www.tumblr.com/oauth/apps`

#### Generate Oauth
```
docker run -it --rm \
    -e CONSUMER_KEY="your_consumer_key" \
    -e CONSUMER_SECRET="your_consumer_secret" \
    jtenniswood/tumblr-oauth:latest
```

#### Paste response
Copy the verifier part of the URL, removing the final "#=*"

`http://localhost:8080/?oauth_token=XXXXXX&oauth_verifier=YYYYYY`

Then copy the oauth key and secrets


## Run

Post state can be: published, draft, queue or private.
Captions can include links but need to be formatted as html.
Gemini image captioning is optional, if you leave it blank it will skip it.
If you don't specify a model, it will default to 'gemini-1.5-flash'.
Finally if you want to use the free gemini credit, you will need to apply a rate limit, so set the upload delay to something like 5 seconds.

```
docker run -d \
  -v /path/to/upload:/data/upload \
  -v /path/to/failed:/data/failed \
  -e CONSUMER_KEY="your_consumer_key" \
  -e CONSUMER_SECRET="your_consumer_secret" \
  -e OAUTH_TOKEN="your_oauth_token" \
  -e OAUTH_SECRET="your_oauth_secret" \
  -e GEMINI_MODEL="" \
  -e GEMINI_API_KEY="" \
  -e UPLOAD_DELAY="" \
  -e BLOG_NAME="your_blog_name" \
  -e POST_STATE="queue" \
  -e COMMON_TAGS="tag1,tag2" \
  -e CAPTION_TEMPLATE="Your caption template" \
  -e CATEGORIES="category1,category2" \
  jtenniswood/tumblr-uploader:latest
```

