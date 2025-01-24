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

# Successful and failed upload paths
COMPLETED_UPLOAD_PATH = "/DATA/complete"
FAILED_UPLOAD_PATH = "/DATA/failed"

def upload_photos_from_folder(folder_path):
    """
    Uploads each image file in `folder_path` to Tumblr as a separate photo post.
    Moves successfully uploaded files to `COMPLETED_UPLOAD_PATH`
    and moves failed uploads to `FAILED_UPLOAD_PATH`.
    """

    # Ensure the required folders exist
    if not os.path.exists(COMPLETED_UPLOAD_PATH):
        os.makedirs(COMPLETED_UPLOAD_PATH)
    if not os.path.exists(FAILED_UPLOAD_PATH):
        os.makedirs(FAILED_UPLOAD_PATH)

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

        # Attempt to create a photo post
        try:
            response = client.create_photo(
                BLOG_NAME,
                state=POST_STATE,
                tags=TAGS,
                caption=caption,
                data=[file_path]
            )
            print(f"Uploaded {filename}: {response}")

            # Check if response indicates success
            # (Here we check if the string 'Posted to tenniswood' is in the response)
            if response and "Posted to tenniswood" in str(response):
                # Success: move to COMPLETED_UPLOAD_PATH
                shutil.move(file_path, os.path.join(COMPLETED_UPLOAD_PATH, filename))
                print(f"Moved {filename} to {COMPLETED_UPLOAD_PATH}")
            else:
                # Failure condition: move to FAILED_UPLOAD_PATH
                shutil.move(file_path, os.path.join(FAILED_UPLOAD_PATH, filename))
                print(f"Moved {filename} to {FAILED_UPLOAD_PATH} (did not match 'Posted to tenniswood')")

        except Exception as e:
            # If there's any error during upload, move to FAILED_UPLOAD_PATH
            print(f"Error uploading {filename}: {e}")
            shutil.move(file_path, os.path.join(FAILED_UPLOAD_PATH, filename))
            print(f"Moved {filename} to {FAILED_UPLOAD_PATH} due to error.")


if __name__ == "__main__":
    upload_photos_from_folder(FOLDER_PATH)
