import os
import time
import shutil
import pytumblr
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------------------
# 1. Tumblr Credentials (EDIT THESE)
# -------------------------------------
CONSUMER_KEY = "YZ5ScnV9ebDVOV5EOZNavNL8fx4NG0RiFFxuQrzcm7ZM4eQx1P"
CONSUMER_SECRET = "B6063TLTtcPVj1M7C2iEYXihVMyMUyZyfvG4BpeLkeRErVY4LQ"
OAUTH_TOKEN = "mgvmTgCmHfoSRZUQhh9JHk7WozWJ6LqKIxmxnOMc2VEYkbLJTI"
OAUTH_SECRET = "OvMFEfydPyWEnL6MxFQ8WR2clAhwpiUmJ5nt0CLOqSNYISqbSM"

# -------------------------------------
# 2. Configuration
# -------------------------------------
BLOG_NAME         = "tenniswood.tumblr.com"
POST_STATE        = "queue"       # "published", "draft", "queue", "private"
COMMON_TAGS       = [""]          # list of tags (currently empty)
CAPTION_TEMPLATE  = "Find more inspiration at https://www.tenniswood.co.uk"

BASE_UPLOAD_FOLDER    = "/DATA/upload"
FAILED_UPLOAD_BASE    = "/DATA/failed"

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
RESET_THRESHOLD    = 5       # If >5 seconds pass with no uploads, we reset
FIRST_FILE_DELAY   = 2       # Delay for the "first" file after idle

FIRST_FILE_HANDLED = False
LAST_UPLOAD_TIME   = time.time()
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

def upload_single_file(file_path, category):
    """
    Upload exactly ONE file to Tumblr as a single photo post (state='queue').
    If upload succeeds, DELETE the file.
    If upload fails, move it to /DATA/failed/<category>.
    """
    # Build subfolder for failures
    failed_upload_path = os.path.join(FAILED_UPLOAD_BASE, category)
    os.makedirs(failed_upload_path, exist_ok=True)

    if not os.path.isfile(file_path):
        print(f"[WARNING] {file_path} is not a valid file.")
        return

    tags = [category] + COMMON_TAGS
    caption = CAPTION_TEMPLATE

    print(f"[UPLOAD] Queuing single file to Tumblr: {file_path}")

    try:
        response = client.create_photo(
            BLOG_NAME,
            state=POST_STATE,   # "queue"
            tags=tags,
            caption=caption,
            data=[file_path]
        )
        print(f"[RESPONSE] {response}")

        if response and 'id' in response:
            # Success: DELETE the file
            print(f"[SUCCESS] Uploaded successfully, deleting original file.")
            os.remove(file_path)
        else:
            # Failure
            print(f"[FAILED] Moving {file_path} -> {failed_upload_path}")
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))

    except Exception as e:
        print(f"[ERROR] {e}")
        if os.path.exists(file_path):
            print(f"[ERROR] Moving {file_path} -> {failed_upload_path}")
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
        if event.is_directory:
            return

        global FIRST_FILE_HANDLED, LAST_UPLOAD_TIME, IDLE_MESSAGE_SHOWN

        file_path = event.src_path
        print(f"[WATCHDOG] New file detected in '{self.category}'")

        # If this is the "first" file in the current active period, wait
        if not FIRST_FILE_HANDLED:
            print(f"[WATCHDOG] Waiting {FIRST_FILE_DELAY}s before uploading")
            time.sleep(FIRST_FILE_DELAY)
            FIRST_FILE_HANDLED = True

        # Upload the file
        upload_single_file(file_path, self.category)

        # Mark ourselves as "active" again
        LAST_UPLOAD_TIME   = time.time()
        IDLE_MESSAGE_SHOWN = False


def watch_folders():
    """
    Sets up Watchdog observers for each category folder.
    Periodically checks if we've been idle for > RESET_THRESHOLD seconds
    to reset logic and show an idle message.
    """
    observers = []

    for category, folder_path in CATEGORIES.items():
        if not os.path.isdir(folder_path):
            print(f"[WARNING] Folder for category '{category}' does not exist: {folder_path}")
            continue

        event_handler = CategoryFolderEventHandler(category, folder_path)
        observer = Observer()

        observer.schedule(event_handler, folder_path, recursive=False)
        observer.start()
        observers.append(observer)

        print(f"[INFO] Watching '{folder_path}' for category '{category}'...")

    try:
        while True:
            time.sleep(1)
            global LAST_UPLOAD_TIME, FIRST_FILE_HANDLED, IDLE_MESSAGE_SHOWN
            idle_time = time.time() - LAST_UPLOAD_TIME

            if idle_time > RESET_THRESHOLD and not IDLE_MESSAGE_SHOWN:
                print(f"[DELAY] Idle for {RESET_THRESHOLD}s. Resetting upload delay.")
                FIRST_FILE_HANDLED = False
                IDLE_MESSAGE_SHOWN = True

    except KeyboardInterrupt:
        print("\n[INFO] Stopping watchers...")
        for obs in observers:
            obs.stop()

    for obs in observers:
        obs.join()


if __name__ == "__main__":
    watch_folders()
