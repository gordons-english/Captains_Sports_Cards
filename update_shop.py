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
        #zoom-modal { 
            transition: opacity 0.3s ease; 
            pointer-events: none; 
            opacity: 0; 
            background-color: rgba(0, 0, 0, 0.9);
        }
        #zoom-modal.active { pointer-events: auto; opacity: 1; }
        
        /* Zoom Lens Container */
        .img-zoom-container {
            position: relative;
            display: inline-block;
        }
        
        #zoom-img {
            max-height: 80vh;
            max-width: 80vw;
            object-fit: contain;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            cursor: none; /* Hide default cursor when hovering */
        }

        .img-zoom-lens {
            position: absolute;
            border: 1px solid #d4d4d4;
            /*set the size of the lens:*/
            width: 100px;
            height: 100px;
            background-color: rgba(255, 255, 255, 0.4);
            border-radius: 50%;
            pointer-events: none; /* Allows clicking through the lens */
            display: none;
            z-index: 1000;
        }

        .img-zoom-result {
            border: 1px solid #d4d4d4;
            /*set the size of the result div:*/
            width: 300px;
            height: 300px;
            position: absolute;
            top: 0;
            left: 105%; /* Position to the right of the image */
            z-index: 1000;
            background-repeat: no-repeat;
            display: none;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            background-color: white;
        }
        
        /* Media query to hide result on small screens or adjust position */
        @media (max-width: 1024px) {
            .img-zoom-result {
                display: none !important; /* Disable lens zoom on mobile/tablets */
            }
            #zoom-img {
                cursor: default;
            }
        }
    </style>
</head>
<body class="bg-gray-100 text-gray-800">

    <!-- ZOOM MODAL -->
    <div id="zoom-modal" class="fixed inset-0 z-[100] flex items-center justify-center p-4" onclick="closeZoom()">
        <div class="relative img-zoom-container" onclick="event.stopPropagation()">
            <img id="zoom-img" src="" class="rounded">
            <div id="zoom-lens" class="img-zoom-lens"></div>
            <div id="zoom-result" class="img-zoom-result"></div>
            <button class="absolute -top-10 right-0 text-white text-4xl hover:text-gray-300 focus:outline-none" onclick="closeZoom()">&times;</button>
        </div>
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
            const match = filename.match(/[\$_ ]([0-9]+\.?[0-9]*)\.(jpg|jpeg|png|webp|gif)$/i);
            return (match && match[1]) ? parseFloat(match[1]) : 0.00;
        }

        function openZoom(src) {
            const modal = document.getElementById('zoom-modal');
            const img = document.getElementById('zoom-img');
            const result = document.getElementById('zoom-result');
            const lens = document.getElementById('zoom-lens');
            
            img.src = src;
            modal.classList.add('active');
            
            // Wait for image to load to initialize zoom
            img.onload = function() {
                initImageZoom(img, result, lens);
            };
        }

        function closeZoom() {
            document.getElementById('zoom-modal').classList.remove('active');
            // Hide zoom elements
            document.getElementById('zoom-result').style.display = "none";
            document.getElementById('zoom-lens').style.display = "none";
        }
        
        function initImageZoom(img, result, lens) {
            let cx, cy;

            // Show elements on mouse enter
            img.addEventListener("mouseenter", function() {
                // Only enable if screen is wide enough
                if (window.innerWidth > 1024) {
                    result.style.display = "block";
                    lens.style.display = "block";
                    
                    // Calculate ratios
                    /* Calculate the ratio between result DIV and lens: */
                    cx = result.offsetWidth / lens.offsetWidth;
                    cy = result.offsetHeight / lens.offsetHeight;

                    /* Set background properties for the result DIV */
                    result.style.backgroundImage = "url('" + img.src + "')";
                    result.style.backgroundSize = (img.width * cx) + "px " + (img.height * cy) + "px";
                }
            });

            // Hide on mouse leave
            img.addEventListener("mouseleave", function() {
                result.style.display = "none";
                lens.style.display = "none";
            });

            lens.addEventListener("mousemove", moveLens);
            img.addEventListener("mousemove", moveLens);
            
            /* And also for touch screens: */
            lens.addEventListener("touchmove", moveLens);
            img.addEventListener("touchmove", moveLens);

            function moveLens(e) {
                if (result.style.display === "none") return;
                
                let pos, x, y;
                /* Prevent any other actions that may occur when moving over the image */
                e.preventDefault();
                /* Get the cursor's x and y positions: */
                pos = getCursorPos(e);
                /* Calculate the position of the lens: */
                x = pos.x - (lens.offsetWidth / 2);
                y = pos.y - (lens.offsetHeight / 2);
                
                /* Prevent the lens from being positioned outside the image: */
                if (x > img.width - lens.offsetWidth) {x = img.width - lens.offsetWidth;}
                if (x < 0) {x = 0;}
                if (y > img.height - lens.offsetHeight) {y = img.height - lens.offsetHeight;}
                if (y < 0) {y = 0;}
                
                /* Set the position of the lens: */
                lens.style.left = x + "px";
                lens.style.top = y + "px";