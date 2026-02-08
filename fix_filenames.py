

import os

# CONFIGURATION
# Only rename these file types to be safe
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def clean_filenames():
    count = 0
    print("--- Checking for files with spaces ---")
    
    # Walk through the current directory and all subfolders
    for root, dirs, files in os.walk("."):
        for filename in files:
            # Check if file has a space
            if " " in filename:
                # Check if it is an image file
                ext = os.path.splitext(filename)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    
                    # Create the new name (replace space with underscore)
                    new_filename = filename.replace(" ", "_")
                    
                    # Full paths
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, new_filename)
                    
                    try:
                        # Rename the file
                        os.rename(old_path, new_path)
                        print(f"✅ Fixed: {filename} -> {new_filename}")
                        count += 1
                    except OSError as e:
                        print(f"❌ Error renaming {filename}: {e}")

    if count == 0:
        print("No files needed fixing. Everything looks good!")
    else:
        print(f"\nSuccessfully renamed {count} files.")

if __name__ == "__main__":
    clean_filenames()
    # Keep window open so user can see what happened
    input("\nPress Enter to exit...")