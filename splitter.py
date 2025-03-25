import os
import logging
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Union
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class LambdaLayerSplitter:
    def __init__(
        self,
        source_dir: Union[str, Path] = 'lambda-layer',
        target_dir: Union[str, Path] = 'python',
        max_part_size: int = 50 * 1024 * 1024,  # 50MB
        buffer_size: int = 1024 * 1024,  # 1MB
        compression_level: int = zipfile.ZIP_DEFLATED
    ):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.max_part_size = max_part_size
        self.buffer_size = buffer_size
        self.compression_level = compression_level
        
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
        if not self.source_dir.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {self.source_dir}")
        if self.max_part_size <= 0:
            raise ValueError("Maximum part size must be a positive integer")

    def process_directory(self) -> None:
        logging.info(f"Processing directory: {self.source_dir}")
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        for item in self.source_dir.rglob('*'):
            if item.is_file():
                self._process_file(item)

    def _process_file(self, source_file: Path) -> None:
        relative_path = source_file.relative_to(self.source_dir)
        target_path = self.target_dir / relative_path
        
        try:
            file_size = source_file.stat().st_size
            if file_size <= self.max_part_size:
                self._copy_file(source_file, target_path)
            else:
                self._split_and_zip_file(source_file, target_path)
        except Exception as e:
            logging.error(f"Failed to process {source_file}: {str(e)}")

    def _copy_file(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        logging.info(f"Copied: {source.relative_to(self.source_dir)}")

    def _split_and_zip_file(self, source: Path, target: Path) -> None:
        original_mtime = source.stat().st_mtime
        part_num = 1
        bytes_written = 0

        with source.open('rb') as src_file:
            while True:
                zip_path = target.with_name(f"{target.name}.part{part_num}.zip")
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(
                    zip_path, 'w', compression=self.compression_level
                ) as zipf:
                    zip_info = zipfile.ZipInfo(str(target.relative_to(self.target_dir)))
                    zip_info.date_time = time.localtime(original_mtime)[:6]
                    zip_info.compress_type = self.compression_level
                    
                    with zipf.open(zip_info, 'w') as dest_file:
                        bytes_written = self._write_chunk(src_file, dest_file)
                
                logging.info(
                    f"Created zip part {part_num} for {source.relative_to(self.source_dir)} "
                    f"({bytes_written / 1024 / 1024:.2f}MB)"
                )
                
                if bytes_written < self.max_part_size:
                    break
                part_num += 1

    def _write_chunk(self, src_file, dest_file) -> int:
        bytes_written = 0
        while bytes_written < self.max_part_size:
            bytes_to_read = min(
                self.buffer_size, 
                self.max_part_size - bytes_written
            )
            chunk = src_file.read(bytes_to_read)
            if not chunk:
                break
            dest_file.write(chunk)
            bytes_written += len(chunk)
        return bytes_written

if __name__ == '__main__':
    try:
        processor = LambdaLayerSplitter(
            max_part_size=50 * 1024 * 1024,  # 50MB
            buffer_size=4 * 1024 * 1024,     # 4MB buffer
            compression_level=zipfile.ZIP_DEFLATED
        )
        processor.process_directory()
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)