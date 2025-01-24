import os
import shutil
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
COMPLETED_UPLOAD_PATH = "/DATA/complete"

def upload_photos_from_folder(folder_path):

    # Ensure the completed-upload folder exists
    if not os.path.exists(COMPLETED_UPLOAD_PATH):
        os.makedirs(COMPLETED_UPLOAD_PATH)

    for filename in os.listdir(folder_path):
        # Skip hidden files / non-image files if necessary
        if filename.startswith('.'):
            continue

        file_path = os.path.join(folder_path, filename)

        # Ensure it's a file (not a directory)
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
                data=[file_path]
            )
            print(f"Uploaded {filename}: {response}")

            # If upload is successful, move file to COMPLETED_UPLOAD_PATH
            shutil.move(file_path, os.path.join(COMPLETED_UPLOAD_PATH, filename))
            print(f"Moved {filename} to {COMPLETED_UPLOAD_PATH} folder.")

        except Exception as e:
            print(f"Error uploading {filename}: {e}")


if __name__ == "__main__":
    upload_photos_from_folder(FOLDER_PATH)
