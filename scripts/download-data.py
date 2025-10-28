#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "requests",
#     "tqdm",
# ]
# ///
"""
Download GIS data for Alexandria, VA backyard chicken zoning map.

This script downloads parcel data, land use codes, and buildings data
from Alexandria's Open Data portal.
"""

import zipfile
from pathlib import Path
import requests
from tqdm import tqdm


# Define data sources
DATASETS = {
    "parcels": {
        "url": "https://hub.arcgis.com/api/v3/datasets/ab8f3a147ddc47deb6d82c5afda65708_0/downloads/data?format=shp&spatialRefId=3857&where=1%3D1",
        "filename": "parcels.zip",
        "extract_dir": "parcels",
    },
    "land_use_codes": {
        "url": "https://hub.arcgis.com/api/v3/datasets/122a2b6d20ea4e1ba8bb831e932ffa56_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1",
        "filename": "land_use_codes.csv",
        "extract_dir": None,
    },
    "buildings": {
        "url": "https://hub.arcgis.com/api/v3/datasets/aec4d1c6ee894e1b821ff39d30bdfc30_0/downloads/data?format=shp&spatialRefId=3857&where=1%3D1",
        "filename": "buildings.zip",
        "extract_dir": "buildings",
    },
    "buildings_use": {
        "url": "https://hub.arcgis.com/api/v3/datasets/8ecb044012bf47f0959fee76e9cc559b_0/downloads/data?format=csv&spatialRefId=3857&where=1%3D1",
        "filename": "buildings-use.csv",
        "extract_dir": None,
    },
    "boundary": {
        "url": "https://services2.arcgis.com/ChYV69FhfjwkvRmy/arcgis/rest/services/Boundary/FeatureServer/replicafilescache/Boundary_-8951757013489615814.zip",
        "filename": "boundary.zip",
        "extract_dir": "boundary",
    },
}


def download_file(url: str, output_path: Path) -> None:
    """
    Download a file from a URL with a progress bar.

    Args:
        url: The URL to download from
        output_path: Path where the file should be saved
    """
    print(f"Downloading {output_path.name}...")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with (
        open(output_path, "wb") as f,
        tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print(f"✓ Downloaded {output_path.name}")


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """
    Extract a zip file to a specified directory.

    Args:
        zip_path: Path to the zip file
        extract_to: Directory to extract contents to
    """
    print(f"Extracting {zip_path.name}...")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    # Remove the zip file after extraction
    zip_path.unlink()

    print(f"✓ Extracted to {extract_to}")


def download_dataset(name: str, config: dict, data_dir: Path) -> None:
    """
    Download and process a single dataset.

    Args:
        name: Name of the dataset
        config: Configuration dictionary with URL and file information
        data_dir: Base data directory
    """
    print(f"\n{'=' * 60}")
    print(f"Processing: {name}")
    print(f"{'=' * 60}")

    filename = config["filename"]
    url = config["url"]
    extract_dir = config.get("extract_dir")

    # Determine output path and what to check for existing data
    if extract_dir:
        output_path = data_dir.joinpath(filename)
        final_dir = data_dir.joinpath(extract_dir)
        check_path = final_dir  # Check if extracted directory exists
    else:
        output_path = data_dir.joinpath(filename)
        final_dir = None
        check_path = output_path  # Check if file exists

    # Skip if data already exists
    if check_path.exists():
        print("⊙ Data already exists, skipping download")
        return

    # Download the file
    download_file(url, output_path)

    # Extract if it's a zip file
    if filename.endswith(".zip") and final_dir:
        final_dir.mkdir(exist_ok=True)
        extract_zip(output_path, final_dir)


def main():
    """Main function to download all GIS datasets."""
    # Get the project root directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root.joinpath("data")

    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)

    print(f"Data will be saved to: {data_dir}")

    # Download all datasets
    for name, config in DATASETS.items():
        try:
            download_dataset(name, config, data_dir)
        except Exception as e:
            print(f"✗ Error downloading {name}: {e}")
            continue

    print(f"\n{'=' * 60}")
    print("✓ All downloads complete!")
    print(f"{'=' * 60}")
    print(f"\nData saved to: {data_dir}")


if __name__ == "__main__":
    main()
