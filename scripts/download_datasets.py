"""
OcuPulse Dataset Download & Verification Utility
Manages acquisition and local directory setup for clinical benchmark datasets:
1. APTOS 2019 Blindness Detection (Kaggle)
2. IDRiD - Indian Diabetic Retinopathy Image Dataset (IEEE Dataport / Grand Challenge)
3. DRIVE - Digital Retinal Images for Vessel Extraction
4. Messidor-2 (ADCIS)
"""

import os
import sys
import json
import argparse
import urllib.request
import zipfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
sys.path.insert(0, PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATASETS_DIR = os.path.join(DATA_DIR, "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)

DATASET_METADATA = {
    "aptos2019": {
        "name": "APTOS 2019 Blindness Detection",
        "description": "3,662 calibrated retinal fundus images with 5-level ICDR severity labels.",
        "url": "https://www.kaggle.com/c/aptos2019-blindness-detection",
        "cli_command": "kaggle competitions download -c aptos2019-blindness-detection -p data/datasets/aptos2019",
        "classes": ["0: No DR", "1: Mild", "2: Moderate", "3: Severe", "4: Proliferative DR"],
        "folder": os.path.join(DATASETS_DIR, "aptos2019")
    },
    "kaggle_dr_2750": {
        "name": "Diabetic Retinopathy Balanced 5-Class Dataset (Sachin Kumar)",
        "description": "2,750 retinal fundus images across 5 classes (Healthy: 1000, Mild: 370, Moderate: 900, Severe: 190, Proliferative: 290).",
        "url": "https://www.kaggle.com/datasets/sachinkumar413/diabetic-retinopathy-dataset",
        "cli_command": "kaggle datasets download -d sachinkumar413/diabetic-retinopathy-dataset -p data/datasets/kaggle_dr_2750 --unzip",
        "classes": [
            "1. Healthy (Not DR): 1,000",
            "2. Mild DR: 370",
            "3. Moderate DR: 900",
            "4. Severe DR: 190",
            "5. Proliferative DR: 290"
        ],
        "folder": os.path.join(DATASETS_DIR, "kaggle_dr_2750")
    },
    "idrid": {
        "name": "IDRiD (Indian Diabetic Retinopathy Image Dataset)",
        "description": "516 clinical fundus scans from eye clinics in India with pixel-level lesion masks.",
        "url": "https://idrid.grand-challenge.org/",
        "cli_command": "Direct academic registration at https://ieeedataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid",
        "features": ["Microaneurysms", "Haemorrhages", "Hard Exudates", "Soft Exudates (Cotton Wool Spots)"],
        "folder": os.path.join(DATASETS_DIR, "idrid")
    },
    "drive": {
        "name": "DRIVE (Digital Retinal Images for Vessel Extraction)",
        "description": "40 standardized retinal photographs with expert manual vessel segmentations.",
        "url": "https://drive.grand-challenge.org/",
        "cli_command": "Download from https://drive.grand-challenge.org/ (training + test zip)",
        "features": ["Vessel Ground Truth", "FOV Mask", "Dual Clinical Observer Segmentations"],
        "folder": os.path.join(DATASETS_DIR, "drive")
    },
    "messidor2": {
        "name": "Messidor-2",
        "description": "1,748 fundus photographs for external validation of referable diabetic retinopathy.",
        "url": "https://www.adcis.net/en/third-party/messidor2/",
        "cli_command": "Download dataset archive from ADCIS: https://www.adcis.net/en/third-party/messidor2/",
        "features": ["Referable DR", "Macular Edema Risk"],
        "folder": os.path.join(DATASETS_DIR, "messidor2")
    }
}


def setup_dataset_directories():
    """Ensures directories and metadata descriptors exist for all benchmark sets."""
    print("📁 Initializing OcuPulse Clinical Benchmark Dataset Folders...")
    for key, info in DATASET_METADATA.items():
        folder = info["folder"]
        os.makedirs(folder, exist_ok=True)
        readme_path = os.path.join(folder, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w") as f:
                f.write(f"# {info['name']}\n\n")
                f.write(f"**URL**: {info['url']}\n\n")
                f.write(f"**Description**: {info['description']}\n\n")
                f.write(f"### Setup Instructions\n")
                f.write(f"```bash\n{info['cli_command']}\n```\n")
        print(f"   ✅ Initialized: {folder}")


def verify_datasets():
    """Scans and reports local status of benchmark datasets."""
    print("\n🔍 Checking Local Dataset Availability:")
    print("=" * 60)
    for key, info in DATASET_METADATA.items():
        folder = info["folder"]
        exists = os.path.isdir(folder)
        file_count = len(os.listdir(folder)) if exists else 0
        status = f"✅ Present ({file_count} files)" if file_count > 1 else "⚠️ Template directory created (Awaiting download)"
        print(f"• {info['name']}:")
        print(f"  Directory: {folder}")
        print(f"  Status:    {status}")
        print(f"  Source:    {info['url']}")
        print()


def generate_sample_drive_pack():
    """Generates synthetic DRIVE verification sample images for offline pipeline testing."""
    drive_folder = DATASET_METADATA["drive"]["folder"]
    images_dir = os.path.join(drive_folder, "images")
    masks_dir = os.path.join(drive_folder, "1st_manual")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(masks_dir, exist_ok=True)

    try:
        from sample_data.sample_generator import generate_synthetic_fundus
    except ImportError:
        from backend.sample_data.sample_generator import generate_synthetic_fundus

    import cv2
    import numpy as np

    print(f"⚡ Generating calibrated benchmark test images in {drive_folder}...")
    for idx in range(1, 6):
        img_name = f"{idx:02d}_test.tif"
        mask_name = f"{idx:02d}_manual1.gif"
        img_path = os.path.join(images_dir, img_name)
        mask_path = os.path.join(masks_dir, mask_name)

        if not os.path.exists(img_path):
            fundus = generate_synthetic_fundus(width=565, height=584, seed=idx * 10)
            cv2.imwrite(img_path, fundus)

        if not os.path.exists(mask_path):
            # Create sample vessel mask
            mask = np.zeros((584, 565), dtype=np.uint8)
            cv2.circle(mask, (282, 292), 240, 255, -1)
            cv2.imwrite(mask_path.replace(".gif", ".png"), mask)

    print("✅ Benchmark test pack ready.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OcuPulse Dataset Manager")
    parser.add_argument("--verify", action="store_true", help="Verify dataset presence")
    parser.add_argument("--setup-dirs", action="store_true", help="Create folder structure")
    parser.add_argument("--generate-test-pack", action="store_true", help="Generate synthetic DRIVE benchmark pack")
    args = parser.parse_args()

    setup_dataset_directories()
    generate_sample_drive_pack()
    verify_datasets()
