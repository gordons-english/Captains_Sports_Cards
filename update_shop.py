import os
import json
import re
import subprocess
import sys

# --- CONFIGURATION ---
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
# Files/Folders to ignore
IGNORE_LIST = {'.git', 'index.html', 'update_shop.py', 'fix_filenames.py', '.DS_Store', 'node_modules', '__pycache__'}

# --- 1. GET THE CORRECT FOLDER (THE FIX) ---
# This tells the script: "I am running inside the CardShop folder. Look HERE."
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def scan_directory(base_path, relative_path=""):
    """Recursively scans directory and builds the inventory object."""
    contents = []
    
    # Path to scan
    current_scan_path = os.path.join(base_path, relative_path)
    
    try:
        items = os.listdir(current_scan_path)
    except OSError as e:
        print(f"Warning: Could not scan {current_scan_path}: {e}")
        return []

    items.sort() # Alphabetical order

    for item in items:
        if item in IGNORE_LIST:
            continue
            
        full_path = os.path.join(current_scan_path, item)
        
        # Calculate the path relative to the script location (for the website link)
        if relative_path:
            item_rel_path = os.path.join(relative_path, item)
        else:
            item_rel_path = item

        if os.path.isdir(full_path):
            folder_obj = {
                "name": item,
                "type": "folder",
                "contents": scan_directory(base_path, item_rel_path)
            }
            if folder_obj["contents"]: # Only add non-empty folders
                contents.append(folder_obj)
                
        elif os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                # Convert backslashes to forward slashes for the web
                web_path = item_rel_path.replace("\\", "/")
                
                file_obj = {
                    "name": web_path,
                    "type": "file",
                    "title": os.path.splitext(item)[0]
                }
                contents.append(file_obj)
    return contents

def update_index_html(inventory_structure):
    """Updates index.html directly using the absolute path."""
    
    # Force it to look in SCRIPT_DIR
    file_path = os.path.join(SCRIPT_DIR, 'index.html')
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Could not find index.html at: {file_path}")
        print("Make sure index.html is in the same folder as this script!")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_inventory_js = f"const inventoryDB = {json.dumps(inventory_structure, indent=4)};"
        pattern = r"const inventoryDB\s*=\s*\{.*?\};"
        
        if not re.search(pattern, content, re.DOTALL):
            print("❌ Error: Could not find 'const inventoryDB = { ... };' inside index.html.")
            return False

        new_content = re.sub(pattern, new_inventory_js, content, count=1, flags=re.DOTALL)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ SUCCESS: Updated index.html")
        return True
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        return False

def push_to_github():
    """Runs git commands using the correct folder context."""
    print("\n--- STARTING GITHUB UPLOAD ---")
    
    # We pass cwd=SCRIPT_DIR to ensure git commands run in the right folder
    try:
        # 1. Add all files
        print("1. Staging files...")
        subprocess.run(["git", "add", "."], check=True, cwd=SCRIPT_DIR)
        
        # 2. Commit changes
        print("2. Committing changes...")
        # Check status
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        if not status.stdout.strip():
            print("   No new changes to upload.")
            return

        subprocess.run(["git", "commit", "-m", "Auto-update inventory"], check=True, cwd=SCRIPT_DIR)
        
        # 3. Push to remote
        print("3. Pushing to GitHub (this may take a moment)...")
        subprocess.run(["git", "push"], check=True, cwd=SCRIPT_DIR)
        
        print("\n✅ DONE! Your website is updating.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR during Git operation: {e}")

def main():
    print(f"--- Working in: {SCRIPT_DIR} ---")
    print("--- SCANNING INVENTORY ---")
    
    # Scan starting from the script's folder
    inventory_structure = {
        "name": "Home",
        "type": "folder",
        "contents": scan_directory(SCRIPT_DIR)
    }
    
    if update_index_html(inventory_structure):
        push_to_github()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()