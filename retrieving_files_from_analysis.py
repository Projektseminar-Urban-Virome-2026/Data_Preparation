import os
import io
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

# Define the URLs for the data sources
source_klima_analysis = "https://github.com/Projektseminar-Urban-Virome-2026/Analysis/tree/65ef960d9bfa70cf61b85e800901f916a0e03c93/data/klima_analyse"

def github_tree_api_url(url):
    """Return the GitHub contents API URL for a /tree/ URL, or None."""
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")

    if parsed.netloc != "github.com" or len(parts) < 5 or parts[2] != "tree":
        return None

    owner, repo, _, ref = parts[:4]
    path = "/".join(parts[4:])
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"


def download_github_directory(api_url, extract_to):
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    items = response.json()

    if not isinstance(items, list):
        raise ValueError(f"GitHub API response is not a directory: {api_url}")

    for item in items:
        item_type = item.get("type")
        item_path = Path(extract_to) / item["name"]

        if item_type == "dir":
            item_path.mkdir(parents=True, exist_ok=True)
            download_github_directory(item["url"], item_path)
        elif item_type == "file":
            file_response = requests.get(item["download_url"], timeout=30)
            file_response.raise_for_status()
            item_path.parent.mkdir(parents=True, exist_ok=True)
            item_path.write_bytes(file_response.content)


def extract_zip(response, extract_to):
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(extract_to)


def download_and_extract(url, extract_to):
    github_api_url = github_tree_api_url(url)

    if github_api_url:
        download_github_directory(github_api_url, extract_to)
        print(f"Data downloaded to {extract_to}")
        return

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    try:
        extract_zip(response, extract_to)
    except zipfile.BadZipFile as exc:
        content_type = response.headers.get("content-type", "unknown")
        raise ValueError(
            f"Expected a ZIP file from {url}, but got content type {content_type}."
        ) from exc

    print(f"Data downloaded and extracted to {extract_to}")


def clear_directory(directory):
    if not os.path.exists(directory):
        return

    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


# Define the directories to save the data
data_dir = "database/data/klima_analysis"

# Create directories if they don't exist
os.makedirs(data_dir, exist_ok=True)

# If the data is already downloaded, delete it to ensure we have the latest version
clear_directory(data_dir)

# Download and extract the data
download_and_extract(source_klima_analysis, data_dir)
