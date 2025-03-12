import requests
import zipfile
import os
import json
import shutil
import time

class AutoUpdater:
    def __init__(self, local_version_path, update_url_base):
        self.local_version_path = local_version_path
        self.update_url_base = update_url_base

    def get_local_version(self):
        with open(self.local_version_path, 'r') as file:
            version_info = json.load(file)
        return version_info['version']

    def check_for_updates(self):
        local_version = self.get_local_version()
        print(f"Current local version: {local_version}")
        try:
            response = requests.get(self.update_url_base + 'XAIBuild.json')
            if response.status_code == 200:
                remote_version_info = response.json()
                remote_version = remote_version_info['version']
                print(f"Remote version available: {remote_version}")
                if remote_version != local_version:
                    return remote_version_info
            return None
        except requests.RequestException as e:
            print(f"Failed to fetch update info: {e}")
            return None

    def download_and_apply_update(self, update_info):
        update_url = update_info['update_url']
        try:
            print("Downloading update package...")
            response = requests.get(update_url)
            with open("update_package.zip", "wb") as file:
                file.write(response.content)

            print("Applying update...")
            with zipfile.ZipFile("update_package.zip", 'r') as zip_ref:
                zip_ref.extractall("update")

            # Assume all files in the update folder should replace the old ones
            for root, dirs, files in os.walk("update"):
                for file in files:
                    shutil.move(os.path.join(root, file), os.path.join(os.getcwd(), file))
            shutil.rmtree("update")  # Cleanup
            print("Update applied successfully. Restarting application...")

            # Restart application logic here if applicable
        except Exception as e:
            print(f"Error during update: {e}")

    def run(self):
        while True:
            update_info = self.check_for_updates()
            if update_info:
                self.download_and_apply_update(update_info)
            else:
                print("No update needed at this time.")
            time.sleep(3600)  # Check for updates every hour

if __name__ == "__main__":
    updater = AutoUpdater("XAIBuild.json", "https://yourserver.com/updates/")
    updater.run()
