import os
import json
import re
import subprocess
import sys

# --- CONFIGURATION ---
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
IGNORE_LIST = {'.git', 'index.html', 'update_shop.py', 'fix_filenames.py', '.DS_Store', 'node_modules', '__pycache__'}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- THE HEADER TEMPLATE (This ensures your text stays!) ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Captain's Sports Cards | Wholesale Vault</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Roboto:wght@400;500;700&display=swap');
        body { font-family: 'Roboto', sans-serif; }
        h1, h2, h3, .brand-font { font-family: 'Oswald', sans-serif; }
        .card-lot { transition: all 0.2s ease; }
        .card-lot:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .card-lot.selected { border: 4px solid #10B981; opacity: 0.9; transform: scale(0.98); }
        .folder-item { transition: all 0.2s ease; cursor: pointer; }
        .folder-item:hover { background-color: #f3f4f6; transform: scale(1.02); }
        
        /* Modal for Zoom */
        #zoom-modal { transition: opacity 0.3s ease; pointer-events: none; opacity: 0; }
        #zoom-modal.active { pointer-events: auto; opacity: 1; }
    </style>
</head>
<body class="bg-gray-100 text-gray-800">

    <!-- ZOOM MODAL -->
    <div id="zoom-modal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-90 p-4" onclick="closeZoom()">
        <img id="zoom-img" src="" class="max-w-full max-h-full rounded shadow-2xl" onclick="event.stopPropagation()">
        <button class="absolute top-4 right-4 text-white text-4xl hover:text-gray-300" onclick="closeZoom()">&times;</button>
    </div>

    <!-- STICKY TOTAL BAR -->
    <div class="fixed top-0 left-0 w-full bg-slate-900 text-white shadow-lg z-50 border-b-4 border-yellow-500">
        <div class="container mx-auto px-4 h-16 flex justify-between items-center">
            <div class="flex items-center space-x-2 cursor-pointer" onclick="goHome()">
                <i class="fa-solid fa-layer-group text-yellow-500 text-xl"></i>
                <span class="text-xl font-bold brand-font tracking-wider">CAPTAIN'S SPORTS CARDS</span>
            </div>
            <div class="flex items-center space-x-6">
                <div class="text-right hidden sm:block">
                    <div class="text-xs text-gray-400 uppercase font-semibold">Current Order Total</div>
                    <div class="text-2xl font-bold text-green-400 font-mono" id="display-total">$0.00</div>
                </div>
                <button id="checkout-btn" onclick="processCheckout()" disabled class="bg-gray-600 text-gray-300 font-bold py-2 px-6 rounded opacity-50 cursor-not-allowed transition-colors text-sm sm:text-base">
                    CHECKOUT ($500 Min)
                </button>
            </div>
        </div>
    </div>

    <!-- SPACING -->
    <div class="h-16"></div>

    <!-- HEADER -->
    <header class="bg-white shadow-sm border-b border-gray-200">
        <div class="container mx-auto px-4 py-8 text-center">
            <h1 class="text-4xl md:text-5xl font-bold text-slate-900 mb-2 uppercase">Wholesale Vault</h1>
            <p class="text-gray-600 max-w-2xl mx-auto">Bulk Card Groups for Dealers & Investors. Browse the folders below.</p>
            
            <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100 inline-block text-left max-w-lg shadow-sm">
                <h3 class="font-bold text-blue-800 mb-2 border-b border-blue-200 pb-1"><i class="fa-solid fa-circle-info mr-2"></i>How It Works:</h3>
                <ul class="text-sm text-blue-900 space-y-2 mt-2">
                    <li class="flex items-start"><i class="fa-solid fa-images mt-1 mr-2 opacity-70"></i> <span><strong>One Image = One Lot:</strong> You are purchasing the entire group of cards shown. We do not pick individual cards.</span></li>
                    <li class="flex items-start"><i class="fa-solid fa-tag mt-1 mr-2 opacity-70"></i> <span><strong>Transparent Pricing:</strong> The price for the lot is listed in the filename (e.g., <code>..._25.00.jpg</code>).</span></li>
                    <li class="flex items-start"><i class="fa-solid fa-calculator mt-1 mr-2 opacity-70"></i> <span><strong>Click Add:</strong> Use the Add button to put the lot in your cart.</span></li>
                </ul>
                <div class="mt-4 pt-3 border-t border-blue-200 text-center">
                    <a href="#" class="text-blue-700 font-bold hover:underline text-xs uppercase tracking-wide">
                        <i class="fa-brands fa-ebay mr-1"></i> Visit eBay Store for Singles
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- BREADCRUMBS -->
    <div class="bg-gray-200 shadow-inner border-b border-gray-300">
        <div class="container mx-auto px-4 py-3 flex items-center space-x-2 text-sm md:text-base overflow-x-auto">
            <button onclick="goHome()" class="text-blue-600 hover:text-blue-800 font-bold"><i class="fa-solid fa-home"></i> Home</button>
            <span class="text-gray-400">/</span>
            <div id="breadcrumbs" class="flex items-center space-x-2 font-medium text-gray-700 whitespace-nowrap"></div>
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <main class="container mx-auto px-4 py-8 pb-24">
        <div id="back-button-container" class="mb-6 hidden">
            <button onclick="goUpLevel()" class="flex items-center text-gray-600 hover:text-slate-900 font-bold transition">
                <i class="fa-solid fa-arrow-left mr-2"></i> Back to Previous Folder
            </button>
        </div>
        <div id="content-grid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"></div>
    </main>

    <!-- LOGIC -->
    <script>
        // --- INVENTORY ---
        const inventoryDB = {INVENTORY_PLACEHOLDER};

        // --- STATE ---
        let currentPath = [];
        let currentFolder = inventoryDB;
        const MINIMUM_ORDER = 500.00;
        let currentTotal = 0.00;
        let selectedLots = new Set();

        // --- FUNCTIONS ---
        function getPriceFromFilename(filename) {
            const match = filename.match(/_([0-9]+\.?[0-9]*)\.(jpg|jpeg|png|webp)$/i);
            return (match && match[1]) ? parseFloat(match[1]) : 0.00;
        }

        function openZoom(src) {
            document.getElementById('zoom-img').src = src;
            document.getElementById('zoom-modal').classList.add('active');
        }

        function closeZoom() {
            document.getElementById('zoom-modal').classList.remove('active');
        }

        function render() {
            const grid = document.getElementById('content-grid');
            const breadcrumbs = document.getElementById('breadcrumbs');
            const backBtn = document.getElementById('back-button-container');
            
            grid.innerHTML = '';
            breadcrumbs.innerHTML = '';

            // Breadcrumbs
            if (currentPath.length === 0) {
                breadcrumbs.innerHTML = '<span class="text-gray-500">Main Vault</span>';
                backBtn.classList.add('hidden');
            } else {
                let html = '';
                currentPath.forEach((folder, index) => {
                    html += `<span class="cursor-pointer hover:underline text-blue-600" onclick="navigateToBreadcrumb(${index})">${folder.name}</span>`;
                    if (index < currentPath.length - 1) html += ` <span class="text-gray-400">/</span> `;
                });
                if (currentPath.length > 0) {
                     html += ` <span class="text-gray-400">/</span> <span class="text-slate-900 font-bold">${currentFolder.name}</span>`;
                }
                breadcrumbs.innerHTML = html;
                backBtn.classList.remove('hidden');
            }

            // Contents
            const contents = currentFolder.contents || [];
            const sortedContents = [...contents].sort((a, b) => {
                if (a.type === b.type) return 0;
                return a.type === 'folder' ? -1 : 1;
            });

            if (sortedContents.length === 0) {
                grid.innerHTML = `<div class="col-span-full text-center py-12 text-gray-400"><i class="fa-regular fa-folder-open text-6xl mb-4"></i><p>This folder is empty.</p></div>`;
                return;
            }

            sortedContents.forEach(item => {
                if (item.type === 'folder') {
                    const folderEl = document.createElement('div');
                    folderEl.className = 'folder-item bg-white p-6 rounded-lg shadow border border-gray-200 flex flex-col items-center justify-center text-center h-48';
                    folderEl.onclick = () => openFolder(item);
                    folderEl.innerHTML = `<i class="fa-solid fa-folder text-6xl text-yellow-500 mb-4"></i><h3 class="text-xl font-bold text-slate-800 truncate w-full" title="${item.name}">${item.name}</h3><p class="text-sm text-gray-500 mt-1">${item.contents ? item.contents.length : 0} Items</p>`;
                    grid.appendChild(folderEl);
                } else {
                    const price = getPriceFromFilename(item.name);
                    const isSelected = selectedLots.has(item.name);
                    const card = document.createElement('div');
                    card.className = `card-lot bg-white rounded-lg shadow overflow-hidden relative ${isSelected ? 'selected' : ''}`;
                    // We removed the onclick from the card container so we can separate zoom and add actions
                    
                    const encodedPath = item.name.split('/').map(encodeURIComponent).join('/');
                    
                    const btnColor = isSelected ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700';
                    const btnText = isSelected ? '<i class="fa-solid fa-times mr-1"></i> Remove' : '<i class="fa-solid fa-cart-plus mr-1"></i> Add';

                    card.innerHTML = `
                        <div class="h-64 bg-slate-200 flex items-center justify-center text-slate-400 relative overflow-hidden group">
                            <img src="${encodedPath}" loading="lazy" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 cursor-pointer" onclick="openZoom('${encodedPath}')" onerror="this.parentElement.innerHTML='<i class=\\'fa-solid fa-image text-4xl\\'></i><span class=\\'ml-2\\'>Image not found</span>'">
                            
                            <!-- Zoom Icon Overlay -->
                            <div class="absolute top-2 right-2 bg-black bg-opacity-60 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer pointer-events-none">
                                <i class="fa-solid fa-magnifying-glass-plus"></i>
                            </div>
                        </div>
                        <div class="p-4">
                            <div class="flex justify-between items-start mb-2">
                                <h3 class="font-bold text-lg text-slate-800 leading-tight truncate pr-2" title="${item.title}">${item.title}</h3>
                                <span class="bg-green-100 text-green-800 text-lg font-bold px-2 py-1 rounded whitespace-nowrap">$${price.toFixed(2)}</span>
                            </div>
                            <!-- Button handles selection separately -->
                            <div class="mt-4 w-full ${btnColor} text-white text-center py-2 rounded font-bold transition shadow-sm cursor-pointer" onclick="toggleSelection('${item.name}', ${price})">${btnText}</div>
                        </div>`;
                    grid.appendChild(card);
                }
            });
        }

        function openFolder(folderObj) { currentPath.push(currentFolder); currentFolder = folderObj; render(); window.scrollTo(0, 0); }
        function goUpLevel() { if (currentPath.length > 0) { currentFolder = currentPath.pop(); render(); } }
        function goHome() { 
            currentPath = []; 
            currentFolder = inventoryDB; 
            render(); 
        }
        function navigateToBreadcrumb(index) { currentFolder = currentPath[index]; currentPath = currentPath.slice(0, index); render(); }

        function toggleSelection(filename, price) {
            // No cardElement passed because we re-render anyway
            if (selectedLots.has(filename)) { selectedLots.delete(filename); currentTotal -= price; } 
            else { selectedLots.add(filename); currentTotal += price; }
            render(); updateTotalDisplay();
        }

        function updateTotalDisplay() {
            currentTotal = Math.max(0, Math.round(currentTotal * 100) / 100);
            document.getElementById('display-total').textContent = '$' + currentTotal.toFixed(2);
            const btn = document.getElementById('checkout-btn');
            if (currentTotal >= MINIMUM_ORDER) {
                btn.disabled = false;
                btn.className = "bg-green-600 hover:bg-green-700 cursor-pointer shadow-lg text-white font-bold py-2 px-6 rounded transition-colors text-sm sm:text-base";
                btn.innerText = `CHECKOUT ($${currentTotal.toFixed(2)})`;
            } else {
                btn.disabled = true;
                btn.className = "bg-gray-600 text-gray-300 font-bold py-2 px-6 rounded opacity-50 cursor-not-allowed transition-colors text-sm sm:text-base";
                btn.innerText = `CHECKOUT ($500 Min)`;
            }
        }

        function processCheckout() {
            if (currentTotal >= MINIMUM_ORDER) {
                const lotCount = selectedLots.size;
                alert(`Proceeding to checkout!\\n\\nLots Selected: ${lotCount}\\nTotal: $${currentTotal.toFixed(2)}`);
            }
        }
        render();
    </script>
</body>
</html>
"""

def scan_directory(base_path, relative_path=""):
    contents = []
    current_scan_path = os.path.join(base_path, relative_path)
    try:
        items = os.listdir(current_scan_path)
    except OSError:
        return []
    items.sort()
    for item in items:
        if item in IGNORE_LIST: continue
        full_path = os.path.join(current_scan_path, item)
        item_rel_path = os.path.join(relative_path, item) if relative_path else item
        
        if os.path.isdir(full_path):
            folder_obj = { "name": item, "type": "folder", "contents": scan_directory(base_path, item_rel_path) }
            if folder_obj["contents"]: contents.append(folder_obj)
        elif os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                web_path = item_rel_path.replace("\\", "/")
                contents.append({ "name": web_path, "type": "file", "title": os.path.splitext(item)[0] })
    return contents

def generate_and_update():
    # 1. Scan
    print("--- Scanning Inventory ---")
    inventory_structure = { "name": "Home", "type": "folder", "contents": scan_directory(SCRIPT_DIR) }
    
    # 2. Inject into Template
    inventory_json = json.dumps(inventory_structure, indent=4)
    final_html = HTML_TEMPLATE.replace("{INVENTORY_PLACEHOLDER}", inventory_json)
    
    # 3. Write index.html
    try:
        with open(os.path.join(SCRIPT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("✅ SUCCESS: Rebuilt index.html with new inventory and header.")
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False
    return True

def push_to_github():
    print("\n--- Uploading to GitHub ---")
    try:
        # Check if remote exists
        remote_check = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        if not remote_check.stdout:
             print("❌ Error: No remote repository configured. Please run 'git remote add origin <URL>' manually first.")
             return

        # Ensure we are on main branch
        subprocess.run(["git", "branch", "-M", "main"], check=True, cwd=SCRIPT_DIR)
        
        # Add all files
        subprocess.run(["git", "add", "."], check=True, cwd=SCRIPT_DIR)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        if not status.stdout.strip():
            print("   No changes to upload.")
            return

        subprocess.run(["git", "commit", "-m", "Auto-update"], check=True, cwd=SCRIPT_DIR)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True, cwd=SCRIPT_DIR)
        print("\n✅ DONE! Website updated.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Git Error: {e}")

if __name__ == "__main__":
    if generate_and_update():
        push_to_github()
    input("\nPress Enter to exit...")