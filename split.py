import os
import shutil

SOURCE_DIR = "/lambda-layer"     # Replace with your source folder
OUTPUT_DIR = "/output"       # Replace with your output folder
MAX_SIZE_BYTES = 50 * 1024 * 1024       # e.g., 50 MB per part

# Verify that SOURCE_DIR exists and print its absolute path
if not os.path.exists(SOURCE_DIR):
    raise FileNotFoundError(f"Source directory not found: {SOURCE_DIR}")
print("Absolute source path:", os.path.abspath(SOURCE_DIR))

# Diagnostic: List all files (including hidden) in the SOURCE_DIR using os.scandir
def list_all_files(directory):
    return [entry.name for entry in os.scandir(directory) if entry.is_file()]

print("Files in SOURCE_DIR:", list_all_files(SOURCE_DIR))

# Create OUTPUT_DIR if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize counters and create the first part folder
part_num = 1
current_size = 0
current_folder = os.path.join(OUTPUT_DIR, f"part_{part_num}")
os.makedirs(current_folder, exist_ok=True)
print(f"Created initial output folder: {current_folder}")

# Walk through SOURCE_DIR without filtering any files
for root, dirs, files in os.walk(SOURCE_DIR):
    # Print diagnostic info about the current folder
    print(f"Walking directory: {root}")
    print(f"Found files: {files}")
    
    for file in files:
        file_path = os.path.join(root, file)
        try:
            file_size = os.path.getsize(file_path)
        except Exception as e:
            print(f"Error getting size for {file_path}: {e}")
            continue

        # If adding the file would exceed the limit, create a new output folder
        if current_size + file_size > MAX_SIZE_BYTES:
            part_num += 1
            current_folder = os.path.join(OUTPUT_DIR, f"part_{part_num}")
            os.makedirs(current_folder, exist_ok=True)
            current_size = 0
            print(f"Starting new part folder: {current_folder}")

        try:
            shutil.copy2(file_path, current_folder)
            current_size += file_size
            print(f"Copied: {file_path} -> {current_folder} | Size: {file_size} bytes | Current part size: {current_size} bytes")
        except Exception as e:
            print(f"Error copying {file_path} to {current_folder}: {e}")

print(f"Splitting complete. Total parts created: {part_num}")
