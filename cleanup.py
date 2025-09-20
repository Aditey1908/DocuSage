"""
Cleanup Script for DocuSage

This script cleans up unnecessary files and organizes the workspace structure.
It removes temporary files, duplicate code, and ensures the project follows
a clean structure.
"""

import os
import shutil
import sys


def clean_directories():
    """Clean up temporary and unnecessary directories"""
    print("Cleaning up temporary directories...")
    
    # Directories to remove
    dirs_to_remove = [
        'thread_documents',
        '__pycache__'
    ]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✓ Removed {dir_name}")
            except Exception as e:
                print(f"✗ Failed to remove {dir_name}: {str(e)}")


def clean_files():
    """Clean up unused or duplicate files"""
    print("\nCleaning up unnecessary files...")
    
    # Files that can be removed (old versions, duplicates, etc.)
    files_to_remove = [
        'app.py',  # Legacy file replaced by docusage.py
        'app_thread.py',  # Legacy file replaced by docusage.py
        'README.md',  # Will be replaced by README_UPDATED.md
    ]
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"✓ Removed {file_name}")
            except Exception as e:
                print(f"✗ Failed to remove {file_name}: {str(e)}")


def rename_files():
    """Rename files for consistency"""
    print("\nRenaming files for consistency...")
    
    # Files to rename (old_name, new_name)
    files_to_rename = [
        ('README_UPDATED.md', 'README.md'),
        ('requirements_updated.txt', 'requirements.txt'),
    ]
    
    for old_name, new_name in files_to_rename:
        if os.path.exists(old_name):
            try:
                # If target exists, remove it first
                if os.path.exists(new_name):
                    os.remove(new_name)
                os.rename(old_name, new_name)
                print(f"✓ Renamed {old_name} to {new_name}")
            except Exception as e:
                print(f"✗ Failed to rename {old_name}: {str(e)}")


def create_required_directories():
    """Create necessary directories if they don't exist"""
    print("\nCreating required directories...")
    
    # Directories to ensure exist
    required_dirs = [
        'data',
        'data/thread_documents',
    ]
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
                print(f"✓ Created {dir_name}")
            except Exception as e:
                print(f"✗ Failed to create {dir_name}: {str(e)}")


def main():
    print("DocuSage Cleanup Utility")
    print("------------------------")
    
    # Check if user wants to proceed
    if input("This will clean up unnecessary files and reorganize the project.\nProceed? (y/n): ").lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Perform cleanup operations
    clean_directories()
    clean_files()
    rename_files()
    create_required_directories()
    
    print("\nCleanup completed successfully!")
    print("\nTo run DocuSage, use: python docusage.py")


if __name__ == "__main__":
    main()
