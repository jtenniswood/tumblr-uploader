import os
import time
import shutil
import logging
import requests
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from requests_oauthlib import OAuth1

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------------
# 1. Tumblr Credentials (Environment Variables)
# -------------------------------------
CONSUMER_KEY    = os.environ.get("CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET", "")
OAUTH_TOKEN     = os.environ.get("OAUTH_TOKEN", "")
OAUTH_SECRET    = os.environ.get("OAUTH_SECRET", "")

# -------------------------------------
# 2. Configuration (Environment Variables)
# -------------------------------------
BLOG_NAME        = os.environ.get("BLOG_NAME", "")  # e.g., "myblog.tumblr.com"
POST_STATE       = os.environ.get("POST_STATE", "") # "published", "draft", "queue", "private"
COMMON_TAGS      = os.environ.get("COMMON_TAGS", "").split(",")  # list of tags (comma-separated)
CAPTION_TEMPLATE = os.environ.get("CAPTION_TEMPLATE", "Find more inspiration at https://www.yourwebsite.com")

# Storage folders
BASE_UPLOAD_FOLDER = os.environ.get("BASE_UPLOAD_FOLDER", "/data/upload")
FAILED_UPLOAD_BASE = os.environ.get("FAILED_UPLOAD_BASE", "/data/failed")

# -------------------------------------
# 2a. Category Names from ENV
# -------------------------------------
# Example: -e CATEGORIES="Gardens,Home,Photography,Technology"
CATEGORIES_STR = os.environ.get("CATEGORIES")
CATEGORY_NAMES = [c.strip() for c in CATEGORIES_STR.split(",") if c.strip()]

# Build a dict that maps category -> full folder path
CATEGORIES = {
    category: os.path.join(BASE_UPLOAD_FOLDER, category)
    for category in CATEGORY_NAMES
}

# -------------------------------------
# 3. Timing Globals & Settings
# -------------------------------------
RESET_THRESHOLD   = 5   # If seconds pass with no uploads, enable upload delay.
FIRST_FILE_DELAY  = 2   # Delay first upload after idle period

FIRST_FILE_HANDLED = False
LAST_UPLOAD_TIME   = time.time()
IDLE_MESSAGE_SHOWN = False

class TumblrAPI:
    def __init__(self, consumer_key, consumer_secret, oauth_token, oauth_secret):
        self.oauth_token = oauth_token
        self.api_base = "https://api.tumblr.com/v2"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_secret = oauth_secret

    def create_photo_post(self, blog_name, file_path, tags=None, caption=None, state="published"):
        url = f"{self.api_base}/blog/{blog_name}/post"
        
        # Prepare the multipart form data
        data = {
            'type': 'photo',
            'state': state,
            'tags': ','.join(tags) if tags else '',
            'caption': caption or ''
        }
        
        # Prepare the file
        with open(file_path, 'rb') as f:
            files = {'data': f}
            
            # Create OAuth1 session with just the credentials
            auth = OAuth1(
                self.consumer_key,
                self.consumer_secret,
                self.oauth_token,
                self.oauth_secret
            )
            
            response = requests.post(url, auth=auth, data=data, files=files)
        
        return response.json()

# Replace the pytumblr client instantiation with our new API client
client = TumblrAPI(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    OAUTH_TOKEN,
    OAUTH_SECRET
)

def upload_single_file(file_path, category):
    """
    Upload exactly ONE file to Tumblr as a single photo post (uses POST_STATE from env).
    If upload succeeds, DELETE the file.
    If upload fails, move it to FAILED_UPLOAD_BASE/<category>.
    """
    # Build subfolder for failures
    failed_upload_path = os.path.join(FAILED_UPLOAD_BASE, category)
    os.makedirs(failed_upload_path, exist_ok=True)

    if not os.path.isfile(file_path):
        logging.warning(f"{file_path} is not a valid file.")
        return

    tags = [category] + COMMON_TAGS
    caption = CAPTION_TEMPLATE

    logging.info(f"Queuing single file to Tumblr: {file_path}")

    try:
        response = client.create_photo_post(
            BLOG_NAME,
            file_path,
            tags=tags,
            caption=caption,
            state=POST_STATE
        )
        logging.info(f"Response: {response}")

        if response and 'response' in response and 'id' in response['response']:
            # Success: DELETE the file
            logging.info(f"Uploaded successfully, deleting original file.")
            os.remove(file_path)
        else:
            # Failure
            logging.warning(f"Upload failed. Response: {response}")
            logging.warning(f"Moving {file_path} -> {failed_upload_path}")
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))

    except Exception as e:
        logging.error(f"Upload error: {e}")
        if os.path.exists(file_path):
            logging.error(f"Moving {file_path} -> {failed_upload_path}")
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))


class CategoryFolderEventHandler(FileSystemEventHandler):
    """
    Watches a specific category folder.
    On new file creation:
      - If FIRST_FILE_HANDLED is False, wait FIRST_FILE_DELAY
      - Then upload that single file
      - Update LAST_UPLOAD_TIME and IDLE_MESSAGE_SHOWN = False (since we're active)
    """
    def __init__(self, category, folder_path):
        super().__init__()
        self.category = category
        self.folder_path = folder_path

    def on_created(self, event):
        logging.info(f"Event detected: {event}")
        if event.is_directory:
            logging.info(f"Skipping directory creation: {event.src_path}")
            return

        global FIRST_FILE_HANDLED, LAST_UPLOAD_TIME, IDLE_MESSAGE_SHOWN

        file_path = event.src_path
        logging.info(f"New file detected in '{self.category}': {file_path}")

        # If this is the "first" file in the current active period, wait
        if not FIRST_FILE_HANDLED:
            logging.info(f"Waiting {FIRST_FILE_DELAY}s before uploading")
            time.sleep(FIRST_FILE_DELAY)
            FIRST_FILE_HANDLED = True

        # Upload the file
        upload_single_file(file_path, self.category)

        # Mark ourselves as "active" again
        LAST_UPLOAD_TIME = time.time()
        IDLE_MESSAGE_SHOWN = False


def watch_folders():
    """
    Sets up PollingObserver (instead of default Observer for better Docker compatibility).
    Periodically checks if we've been idle for > RESET_THRESHOLD seconds
    to reset logic and show an idle message.
    """
    observers = []

    for category, folder_path in CATEGORIES.items():
        if not os.path.isdir(folder_path):
            logging.warning(f"Folder for category '{category}' does not exist: {folder_path}")
            continue

        event_handler = CategoryFolderEventHandler(category, folder_path)
        observer = PollingObserver()

        observer.schedule(event_handler, folder_path, recursive=False)
        observer.start()
        observers.append(observer)

        logging.info(f"Watching '{folder_path}' for category '{category}'...")

    try:
        while True:
            time.sleep(1)
            global LAST_UPLOAD_TIME, FIRST_FILE_HANDLED, IDLE_MESSAGE_SHOWN
            idle_time = time.time() - LAST_UPLOAD_TIME

            if idle_time > RESET_THRESHOLD and not IDLE_MESSAGE_SHOWN:
                logging.info(f"Idle for {RESET_THRESHOLD}s. Resetting upload delay.")
                FIRST_FILE_HANDLED = False
                IDLE_MESSAGE_SHOWN = True

    except KeyboardInterrupt:
        logging.info("Stopping watchers...")
        for obs in observers:
            obs.stop()

    for obs in observers:
        obs.join()


def manual_poll_folders():
    """
    Alternative method: Instead of using watch_folders(),
    you could poll the folders manually every X seconds.
    """
    while True:
        for category, folder_path in CATEGORIES.items():
            if not os.path.isdir(folder_path):
                logging.warning(f"Folder for category '{category}' does not exist: {folder_path}")
                continue

            files = os.listdir(folder_path)
            for file_name in files:
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    logging.info(f"Detected file in manual poll: {file_path}")
                    upload_single_file(file_path, category)

        time.sleep(5)  # Adjust polling interval as desired


if __name__ == "__main__":
    # Create base directories if they don't exist
    os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(FAILED_UPLOAD_BASE, exist_ok=True)
    # Create category subfolders
    for category in CATEGORY_NAMES:
        os.makedirs(os.path.join(BASE_UPLOAD_FOLDER, category), exist_ok=True)

    # Choose which method you prefer:
    watch_folders()
    # or:
    # manual_poll_folders()
