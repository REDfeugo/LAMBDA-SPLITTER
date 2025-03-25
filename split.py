import os
import shutil

def split_files(source_dir='lambda-layer', target_dir='python', chunk_size=50*1024*1024):
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            source_path = os.path.join(root, file)
            
            # Get relative path to maintain directory structure
            relative_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, relative_path)
            
            # Create target directory structure
            target_parent = os.path.dirname(target_path)
            os.makedirs(target_parent, exist_ok=True)
            
            file_size = os.path.getsize(source_path)
            
            if file_size <= chunk_size:
                # Copy file directly if under chunk size
                shutil.copy2(source_path, target_path)
                print(f"Copied: {relative_path}")
            else:
                # Split file into chunks
                part_num = 1
                with open(source_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        part_filename = f"{target_path}.part{part_num}"
                        with open(part_filename, 'wb') as part_file:
                            part_file.write(chunk)
                        print(f"Created part: {os.path.relpath(part_filename, target_dir)}")
                        part_num += 1

if __name__ == '__main__':
    split_files()
    print("File splitting completed!")