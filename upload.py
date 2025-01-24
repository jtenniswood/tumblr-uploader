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
UPLOAD_DELAY    = 2    # Changed to 2 seconds
BLOG_NAME       = "tenniswood.tumblr.com"
POST_STATE      = "published"  # "published", "draft", "queue", "private"
COMMON_TAGS     = [""]         # list of tags (currently empty)
CAPTION_TEMPLATE = "Find more inspiration at https://www.tenniswood.co.uk"

# Base folders (EDIT THESE as needed)
BASE_UPLOAD_FOLDER    = "/DATA/upload"
COMPLETED_UPLOAD_BASE = "/DATA/complete"
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
# 3. Instantiate the Tumblr client
# -------------------------------------
client = pytumblr.TumblrRestClient(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    OAUTH_TOKEN,
    OAUTH_SECRET
)

def upload_single_file(file_path, category):
    """
    Upload exactly ONE file to Tumblr as a single photo post.
    Move the file to /DATA/complete/<category> on success,
    or /DATA/failed/<category> on failure.
    """
    # Build subfolders for completed/failed
    completed_upload_path = os.path.join(COMPLETED_UPLOAD_BASE, category)
    failed_upload_path    = os.path.join(FAILED_UPLOAD_BASE, category)
    os.makedirs(completed_upload_path, exist_ok=True)
    os.makedirs(failed_upload_path, exist_ok=True)

    # Double-check that file_path is a valid file
    if not os.path.isfile(file_path):
        print(f"[WARNING] {file_path} is not a valid file.")
        return

    # Generate tags (category + any common tags)
    tags = [category] + COMMON_TAGS

    # Use a static caption or adjust as needed
    caption = CAPTION_TEMPLATE

    print(f"[UPLOAD] Attempting to post single file to Tumblr: {file_path}")

    try:
        response = client.create_photo(
            BLOG_NAME,
            state=POST_STATE,
            tags=tags,
            caption=caption,
            data=[file_path]  # single-file upload
        )
        print(f"[RESPONSE] {response}")

        # Check if the response indicates success (assuming 'id' in response => success)
        if response and 'id' in response:
            # Success: move the file to completed_upload_path
            shutil.move(file_path, os.path.join(completed_upload_path, os.path.basename(file_path)))
            print(f"[SUCCESS] Moved {file_path} -> {completed_upload_path}")
        else:
            # Otherwise, treat as failure
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))
            print(f"[FAILED] Moved {file_path} -> {failed_upload_path}")

    except Exception as e:
        # If there's any error, move the file to the 'failed' folder
        print(f"[ERROR] {e}")
        if os.path.exists(file_path):
            shutil.move(file_path, os.path.join(failed_upload_path, os.path.basename(file_path)))
            print(f"[ERROR] Moved {file_path} -> {failed_upload_path}")

class CategoryFolderEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a given 'category' folder.
    Whenever a new file is created, we wait UPLOAD_DELAY seconds,
    then upload that single file to Tumblr.
    """
    def __init__(self, category, folder_path):
        super().__init__()
        self.category = category
        self.folder_path = folder_path

    def on_created(self, event):
        # Only act on files (not subdirectories)
        if not event.is_directory:
            file_path = event.src_path
            print(f"[WATCHDOG] New file detected: {file_path} in '{self.category}'")

            # Wait UPLOAD_DELAY seconds before uploading
            print(f"[WATCHDOG] Waiting {UPLOAD_DELAY}s before uploading '{file_path}'...")
            time.sleep(UPLOAD_DELAY)

            # Then upload this single file
            upload_single_file(file_path, self.category)


def watch_folders():
    """
    Create a Watchdog observer for each category/folder pair,
    so that new files in those folders automatically get uploaded (one post per file).
    """
    observers = []

    for category, folder_path in CATEGORIES.items():
        if not os.path.isdir(folder_path):
            print(f"[WARNING] Folder for category '{category}' does not exist: {folder_path}")
            continue

        event_handler = CategoryFolderEventHandler(category, folder_path)
        observer = Observer()

        # Monitor changes in `folder_path` (non-recursive = just that folder)
        observer.schedule(event_handler, folder_path, recursive=False)
        observer.start()
        observers.append(observer)

        print(f"[INFO] Watching '{folder_path}' for category '{category}'...")

    # Keep the script running indefinitely
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping watchers...")
        for obs in observers:
            obs.stop()

    for obs in observers:
        obs.join()


if __name__ == "__main__":
    watch_folders()
