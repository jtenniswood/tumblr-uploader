import os
import pytumblr

# -------------------------------------
# 1. Fill in your Tumblr credentials
# -------------------------------------
CONSUMER_KEY = "YZ5ScnV9ebDVOV5EOZNavNL8fx4NG0RiFFxuQrzcm7ZM4eQx1P"
CONSUMER_SECRET = "B6063TLTtcPVj1M7C2iEYXihVMyMUyZyfvG4BpeLkeRErVY4LQ"
OAUTH_TOKEN = "mgvmTgCmHfoSRZUQhh9JHk7WozWJ6LqKIxmxnOMc2VEYkbLJTI"
OAUTH_SECRET = "OvMFEfydPyWEnL6MxFQ8WR2clAhwpiUmJ5nt0CLOqSNYISqbSM"

# -------------------------------------
# 2. Instantiate the Tumblr client
# -------------------------------------
client = pytumblr.TumblrRestClient(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    OAUTH_TOKEN,
    OAUTH_SECRET
)

# -------------------------------------
# 3. Configuration
# -------------------------------------
BLOG_NAME = "tenniswood.tumblr.com"  # e.g. "myblog.tumblr.com" (without http/https)
FOLDER_PATH = "/DATA/images/"  # local path to your folder of images
POST_STATE = "published"  # or "draft", "queue", "private"
TAGS = ["test"]  # tags to include in each post
CAPTION_TEMPLATE = "Test"  # optional: caption format

# -------------------------------------
# 4. Iterate over local images and create photo posts
# -------------------------------------
def upload_photos_from_folder(folder_path):
    """Uploads each image file in `folder_path` to Tumblr as a separate photo post."""
    for filename in os.listdir(folder_path):
        # Skip hidden files / non-image files if necessary
        if filename.startswith('.'):
            continue

        # Full path to the file
        file_path = os.path.join(folder_path, filename)

        # Check if it's actually a file
        if not os.path.isfile(file_path):
            continue

        # Optionally filter by file extension:
        # if not (filename.lower().endswith(".jpg") or filename.lower().endswith(".png")):
        #     continue

        # Generate a caption (optional)
        caption = CAPTION_TEMPLATE.format(filename)

        # Create a photo post
        try:
            response = client.create_photo(
                BLOG_NAME,
                state=POST_STATE,
                tags=TAGS,
                caption=caption,
                data=[file_path]  # List of image paths if you want multiple images in one post
            )
            print(f"Uploaded {filename}: {response}")
        except Exception as e:
            print(f"Error uploading {filename}: {e}")

if __name__ == "__main__":
    upload_photos_from_folder(FOLDER_PATH)
