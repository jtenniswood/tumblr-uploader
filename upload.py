import os
import time
import shutil
import pytumblr
import logging
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------------
# 1. Tumblr Credentials (Environment Variables)
# -------------------------------------
CONSUMER_KEY = os.environ.get("CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET", "")
OAUTH_TOKEN = os.environ.get("OAUTH_TOKEN", "")
OAUTH_SECRET = os.environ.get("OAUTH_SECRET", "")

# -------------------------------------
# 2. Configuration
# -------------------------------------
BLOG_NAME = os.environ.get("BLOG_NAME", "") # "blogname.tumblr.com
POST_STATE = os.environ.get("POST_STATE", "")  # "published", "draft", "queue", "private"
COMMON_TAGS = os.environ.get("COMMON_TAGS", "").split(",")  # list of tags (comma-separated)
CAPTION_TEMPLATE = os.environ.get("CAPTION_TEMPLATE", "Find more inspiration at https://www.yourwebsite.com")

# Storage folders
BASE_UPLOAD_FOLDER = os.environ.get("BASE_UPLOAD_FOLDER", "/data/upload")
FAILED_UPLOAD_BASE = os.environ.get("FAILED_UPLOAD_BASE", "/data/failed")

# Category names (subfolders under BASE_UPLOAD_FOLDER)
CATEGORY_NAMES = [
    "gardens",
    "home",
    "photography",
    "technology"
]

# Build a dict that maps category -> full folder path
CATEGORIES = {
    category: os.path.join(BASE_UPLOAD_FOLDER, category)
    for category in CATEGORY_NAMES
}

# -------------------------------------
# 3. Timing Globals & Settings
# -------------------------------------
RESET_THRESHOLD = 5  # If seconds pass with no uploads, enable upload delay.
FIRST_FILE_DELAY = 2  # Delay first update after idle

FIRST_FILE_HANDLED = False
LAST_UPLOAD_TIME = time.time()
IDLE_MESSAGE_SHOWN = False

# -------------------------------------
# 4. Instantiate the Tumblr client
# -------------------------------------
client = pytumblr.TumblrRestClient(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    OAUTH_TOKEN,
    OAUTH_SECRET
)

"""
Upload a file from a folder to the matching category
"""

def upload_single_file(file_path, category):
    """
    Upload exactly ONE file to Tumblr as a single photo post (state='queue').
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
        response = client.create_photo(
            BLOG_NAME,
            state=POST_STATE,  # "queue"
            tags=tags,
            caption=caption,
            data=[file_path]
        )
        logging.info(f"Response: {response}")

        if response and 'id' in response:
            # Success: DELETE the file
            logging.info(f"Uploaded successfully, deleting original file.")
            os.remove(file_path)
        else:
            # Failure
            logging.warning(f"Moving {file_path} -> {failed_upload_path}")
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))

    except Exception as e:
        logging.error(f"{e}")
        if os.path.exists(file_path):
            logging.error(f"Moving {file_path} -> {failed_upload_path}")
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))


"""
Watches a specific category folder.
On new file creation:
  - If FIRST_FILE_HANDLED is False, wait FIRST_FILE_DELAY
  - Then upload that single file
  - Update LAST_UPLOAD_TIME and IDLE_MESSAGE_SHOWN = False (since we're active)
"""

class CategoryFolderEventHandler(FileSystemEventHandler):
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


"""
Sets up Watchdog observers for each category folder.
Periodically checks if we've been idle for > RESET_THRESHOLD seconds
to reset logic and show an idle message.
"""

def watch_folders():
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

        time.sleep(5)  # Adjust polling interval


if __name__ == "__main__":
    os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(FAILED_UPLOAD_BASE, exist_ok=True)
    for category in CATEGORY_NAMES:
        os.makedirs(os.path.join(BASE_UPLOAD_FOLDER, category), exist_ok=True)
    # Replace watch_folders() with manual_poll_folders() if needed
    watch_folders()

