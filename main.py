#!/usr/bin/env python3
"""
main.py

Reads all files from /lambda-layer and splits them into chunks
where each chunk's total size is <= 50 bytes. For each chunk, 
this script creates a subfolder (python1, python2, etc.) in /python
and copies the chunk's files there. It also creates a zip file
named python_part_{n}.zip in the same /python directory.

Usage:
    python main.py
"""

import os
import shutil
import zipfile

# -----------------------------------------
# Configuration
# -----------------------------------------
SOURCE_DIR = "/lambda-layer"  # Where your files are
OUTPUT_DIR = "/python"        # Where subfolders & zip files will be placed
MAX_SIZE = 50                 # Max total size per chunk in bytes (demo: 50)

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def list_files_with_size(source_dir):
    """
    Returns a list of (abs_path, rel_path, file_size) for every file in source_dir.
    """
    all_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, source_dir)
            size = os.path.getsize(abs_path)
            all_files.append((abs_path, rel_path, size))
    return all_files

def split_files_by_size(files, max_size):
    """
    Splits 'files' into chunks so each chunk's total file size <= max_size.
    Each file is a tuple (abs_path, rel_path, size).
    Returns a list of chunks (each chunk is a list of these tuples).
    """
    chunks = []
    current_chunk = []
    current_sum = 0

    for abs_path, rel_path, size in files:
        # If adding this file exceeds max_size and we already have some files in current_chunk
        if current_chunk and (current_sum + size > max_size):
            chunks.append(current_chunk)
            current_chunk = []
            current_sum = 0
        
        current_chunk.append((abs_path, rel_path, size))
        current_sum += size

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def copy_files_to_folder(chunk, destination_folder):
    """
    Copy files from the chunk into 'destination_folder', preserving directory structure.
    """
    for abs_path, rel_path, _ in chunk:
        out_file = os.path.join(destination_folder, rel_path)
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        shutil.copy2(abs_path, out_file)

def create_zip_from_folder(folder_path, zip_path):
    """
    Create a zip file at zip_path from the contents of folder_path.
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                # arcname ensures the subfolder (e.g., python1/...) structure is preserved
                arcname = os.path.relpath(full_path, os.path.dirname(folder_path))
                zipf.write(full_path, arcname)

# -----------------------------------------
# Main Function
# -----------------------------------------
def main():
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. List files from SOURCE_DIR
    files = list_files_with_size(SOURCE_DIR)
    total_files = len(files)
    print(f"Found {total_files} file(s) in '{SOURCE_DIR}'.")

    if total_files == 0:
        print("No files found. Exiting.")
        return

    # 2. Split files by total size
    chunks = split_files_by_size(files, MAX_SIZE)
    print(f"Splitting into {len(chunks)} part(s), up to {MAX_SIZE} bytes each.")

    # 3. For each chunk, create a subfolder "python{n}" and zip it
    for idx, chunk in enumerate(chunks, start=1):
        # The subfolder name, e.g. /python/python1
        subfolder_name = f"python{idx}"
        subfolder_path = os.path.join(OUTPUT_DIR, subfolder_name)
        os.makedirs(subfolder_path, exist_ok=True)
        
        # Copy chunk files into that subfolder
        copy_files_to_folder(chunk, subfolder_path)
        
        # Create the zip file in the same output directory
        zip_filename = f"python_part_{idx}.zip"
        zip_filepath = os.path.join(OUTPUT_DIR, zip_filename)
        create_zip_from_folder(subfolder_path, zip_filepath)
        
        print(f"Created {zip_filename} in {OUTPUT_DIR} with {len(chunk)} file(s). "
              f"Folder: {subfolder_name}")

    print("Done! Check the /python directory to see each 'pythonN' folder and corresponding zip.")

if __name__ == "__main__":
    main()
