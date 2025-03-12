import requests
import json
import os
import shutil
import configparser
from dotenv import load_dotenv  

# Local XAIBuild.json path
XAIBUILD_LOCAL = "XAIBuild.json"
# Firebase Hosting URL for XAIBuild.json
XAIBUILD_REMOTE_URL = "https://github.com/RedXDevelopment/Red-XAIPortal/raw/main/XAIBuild.json"
EnvVars=load_dotenv('config/.env')
GitHubToken = os.getenv('GitHubToken')
# Config file
INSTALLER_CFG = "installer.cfg"
def get_remote_xaibuild():
    """Fetches the latest XAIBuild.json from Firebase Hosting"""
    try:
        response = requests.get(XAIBUILD_REMOTE_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching remote XAIBuild.json: {e}")
        return None

def get_local_xaibuild():
    """Reads the local XAIBuild.json file"""
    if not os.path.exists(XAIBUILD_LOCAL):
        return None
    with open(XAIBUILD_LOCAL, "r") as f:
        return json.load(f)

def get_install_path():
    """Reads the install path from installer.cfg (if needed)"""
    if not os.path.exists(INSTALLER_CFG):
        print("Warning: installer.cfg not found. Using default paths.")
        return os.getcwd()
    
    config = configparser.ConfigParser()
    config.read(INSTALLER_CFG)

    return config.get("Installation", "InstallPath", fallback=os.getcwd())

def download_file(url, destination, GitHubToken):
    """Downloads a file from GitHub using a personal access token."""
    try:
        headers = {'Authorization': f'token {GitHubToken}'}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Downloaded: {destination}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

def apply_changes(remote_data, install_path, GitHubToken):
    base_url = remote_data.get("BaseUrl", "")

    # Handle deletions
    for file_path in remote_data["Files"].get("delete", []):
        full_path = os.path.join(install_path, file_path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            print(f"Deleted: {full_path}")

    # Handle additions
    for file_path in remote_data["Files"].get("add", []):
        dest_path = os.path.join(install_path, file_path)
        download_file(base_url + file_path, dest_path, GitHubToken)

    # Handle modifications
    for file_path in remote_data["Files"].get("modify", []):
        dest_path = os.path.join(install_path, file_path)
        download_file(base_url + file_path, dest_path, GitHubToken)

    # Update local XAIBuild.json
    with open(XAIBUILD_LOCAL, "w") as f:
        json.dump(remote_data, f, indent=4)

def check_for_updates():
    remote_data = get_remote_xaibuild()
    local_data = get_local_xaibuild()

    if not remote_data or not local_data:
        return

    install_path = get_install_path()
    GitHubToken = os.getenv("GitHubToken")

    if remote_data["AppVersion"] > local_data["AppVersion"]:
        print(f"New update available: {remote_data['AppVersion']}")
        apply_changes(remote_data, install_path, GitHubToken)
        print("Update applied successfully.")


if __name__ == "__main__":
    check_for_updates()
