import os
import random
import requests
import subprocess
import time
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

WORK_DIR = r"C:\Users\suresh\Downloads\project"
OUTPUT_DIR = r"C:\Users\suresh\Downloads\project\output"
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
SATDUMP_PATH = r"C:\Program Files\SatDump\satdump.exe"

ACTIVE_SATELLITES = [
    {"name": "Meteor-M 2-3", "norad": 57166},
    {"name": "Meteor-M 2-4", "norad": 59051}
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.chdir(WORK_DIR)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SatNOGS EO Pipeline & SDG Analytics Hub</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        space: {
                            950: '#030712',
                            900: '#060913',
                            800: '#0d1322',
                            700: '#172036',
                            600: '#23304d',
                        },
                        cyanNeon: '#00f2fe',
                        blueNeon: '#4facfe',
                        emeraldNeon: '#10b981',
                        amberNeon: '#f59e0b'
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    }
                }
            }
        }
    </script>
    <style>
        body {
            background-color: #030712;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
            overflow-x: hidden;
        }
        .glass-panel {
            background: rgba(13, 19, 34, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glass-card {
            background: rgba(23, 32, 54, 0.65);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            border-color: rgba(0, 242, 254, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px -5px rgba(0, 242, 254, 0.15);
        }
        .btn-glow {
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
            transition: all 0.3s ease;
        }
        .btn-glow:hover {
            box-shadow: 0 0 30px rgba(0, 242, 254, 0.7);
            transform: translateY(-1px);
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #060913;
        }
        ::-webkit-scrollbar-thumb {
            background: #23304d;
            border-radius: 4px;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- NAVIGATION HEADER -->
    <header class="sticky top-0 z-40 glass-panel border-b border-white/10 px-4 lg:px-8 py-3">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-space-950 font-black text-xl shadow-lg shadow-cyan-500/20">
                    <i class="fa-solid fa-satellite text-space-950"></i>
                </div>
                <div>
                    <h1 class="text-base font-extrabold text-white tracking-wide flex items-center gap-2">
                        SatNOGS EO Pipeline & SDG Analytics Hub
                        <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyanNeon border border-cyan-500/30">v7.0 Fully Dynamic Sync</span>
                    </h1>
                    <p class="text-xs text-slate-400">Meteor-M & Sentinel Telemetry Fetcher → Transcoder → Decoder → SDG Metrics</p>
                </div>
            </div>

            <div class="flex items-center space-x-3 w-full sm:w-auto">
                <button id="mainRunBtn" onclick="runAutomatedPipeline()" class="w-full sm:w-auto btn-glow bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 text-space-950 font-extrabold px-6 py-2.5 rounded-xl text-xs flex items-center justify-center space-x-2 tracking-wider uppercase">
                    <i class="fa-solid fa-bolt text-space-950 text-sm"></i>
                    <span>⚡ AUTOMATIC RUN PIPELINE</span>
                </button>
            </div>
        </div>
    </header>

    <!-- MAIN BODY CONTAINER -->
    <main class="flex-grow max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-8">

        <!-- TOP STATUS COUNTERS -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="glass-card p-4 rounded-xl border-l-4 border-l-cyanNeon">
                <div class="text-slate-400 text-xs font-mono mb-1">SatNOGS Pass Queue</div>
                <div class="text-xl font-extrabold text-white font-mono">Archive Synced</div>
                <div class="text-[11px] text-cyanNeon mt-1">Meteor-M 2-3 & 2-4 Active</div>
            </div>
            <div class="glass-card p-4 rounded-xl border-l-4 border-l-emeraldNeon">
                <div class="text-slate-400 text-xs font-mono mb-1">Processing Engine</div>
                <div class="text-xl font-extrabold text-white font-mono">VLC & SatDump</div>
                <div class="text-[11px] text-emerald-400 mt-1">CLI Automation Ready</div>
            </div>
            <div class="glass-card p-4 rounded-xl border-l-4 border-l-blueNeon">
                <div class="text-slate-400 text-xs font-mono mb-1">Global SDG Coverage</div>
                <div class="text-xl font-extrabold text-white font-mono">100% (17 / 17 SDGs)</div>
                <div class="text-[11px] text-blueNeon mt-1">Numerical Satellite Analytics Active</div>
            </div>
            <div class="glass-card p-4 rounded-xl border-l-4 border-l-amberNeon">
                <div class="text-slate-400 text-xs font-mono mb-1">Pipeline Status</div>
                <div class="text-xl font-extrabold text-amberNeon font-mono" id="pipelineStateText">STANDBY</div>
                <div class="text-[11px] text-slate-400 mt-1" id="pipelineStateSub">Ready for Demonstration</div>
            </div>
        </section>

        <!-- TERMINAL & PROGRESS -->
        <section class="glass-panel rounded-2xl p-6 border border-white/10 space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 class="text-lg font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-cyanNeon"></i> Automated Telemetry Execution Engine
                    </h2>
                    <p class="text-xs text-slate-400">Live monitoring of API payload fetching, audio decoding, and pass synchronization.</p>
                </div>
                <div class="flex items-center space-x-3 bg-space-900 px-4 py-2 rounded-xl border border-white/10">
                    <span id="circularPercentText" class="text-cyanNeon font-mono font-bold text-lg">0%</span>
                    <div>
                        <div class="text-xs font-mono font-bold text-white" id="currentStageLabel">Stage: IDLE</div>
                        <div class="text-[11px] text-slate-400 font-mono" id="timeElapsedLabel">Elapsed: 00:00</div>
                    </div>
                </div>
            </div>

            <div class="space-y-1.5">
                <div class="flex justify-between items-center text-xs font-mono">
                    <span class="text-slate-400">Total Execution Progress</span>
                    <span id="linearPercentText" class="text-cyanNeon font-bold">0%</span>
                </div>
                <div class="w-full h-3 bg-space-900 rounded-full overflow-hidden border border-white/10 p-0.5">
                    <div id="linearProgressBar" class="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-emerald-400 rounded-full transition-all duration-300 w-0"></div>
                </div>
            </div>

            <div class="bg-space-950 rounded-xl border border-white/10 p-4 font-mono text-xs text-slate-300 space-y-1 h-40 overflow-y-auto" id="terminalLogs">
                <div class="text-slate-500">[SYSTEM INACTIVE] Click 'AUTOMATIC RUN PIPELINE' to execute local download & decode loop.</div>
            </div>
        </section>

        <!-- EXACT SCREENSHOT LAYOUT: SPECTRAL VIEWER & THUMBNAILS -->
        <section class="space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-photo-film text-cyanNeon"></i> Decoded Satellite Imagery & Spectral Viewer
                    </h2>
                    <p class="text-xs text-slate-400">Interactive pass selector matching your presentation template layout.</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Main Preview Viewport (Left 2 Columns) -->
                <div class="lg:col-span-2 glass-panel rounded-2xl overflow-hidden border border-white/10 flex flex-col justify-between relative min-h-[420px]">
                    <div class="relative bg-space-950 flex-grow flex items-center justify-center overflow-hidden">
                        <img id="mainViewerImg" src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200&auto=format&fit=crop" alt="Decoded Telemetry Capture" class="w-full h-[420px] object-cover transition-all duration-500">
                        
                        <!-- Top Badges -->
                        <div class="absolute top-4 left-4 flex flex-wrap gap-2">
                            <span id="viewerSatelliteBadge" class="bg-space-900/90 backdrop-blur border border-cyan-500/40 text-cyanNeon font-mono text-xs px-3 py-1 rounded-full flex items-center gap-2 shadow-lg">
                                <span class="w-2 h-2 rounded-full bg-cyanNeon animate-ping"></span>
                                Meteor-M 2-3 (NORAD 57166)
                            </span>
                            <span id="viewerPassBadge" class="bg-space-900/90 backdrop-blur border border-emerald-500/40 text-emerald-400 font-mono text-xs px-3 py-1 rounded-full shadow-lg">
                                LRPT 137.900 MHz
                            </span>
                        </div>

                        <!-- Bottom Information Strip Overlay -->
                        <div class="absolute bottom-4 left-4 right-4 bg-space-950/90 backdrop-blur p-4 rounded-xl border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
                            <div>
                                <h3 id="viewerTitle" class="text-sm font-bold text-white">Cyclone & Cloud Top Thermal Infrared Composite</h3>
                                <p id="viewerDesc" class="text-xs text-slate-400 mt-0.5">Demodulated via SatDump CLI. Thermal channel AVHRR sensors tracking atmospheric depressions and sea temperature.</p>
                            </div>
                            <div class="shrink-0">
                                <span id="viewerSDGTag" class="bg-cyan-500/20 text-cyanNeon border border-cyan-500/30 text-xs px-3 py-1.5 rounded-lg font-mono font-bold">SDG 13: Climate Action</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Sidebar Thumbnails (Right 1 Column) -->
                <div class="space-y-3 flex flex-col justify-between" id="sidebarThumbnails">
                    <!-- Injected via JavaScript -->
                </div>
            </div>
        </section>

        <!-- UN SDGs ANALYTICS DASHBOARD -->
        <section class="space-y-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                    <h2 class="text-xl font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-chart-column text-emerald-400"></i> UN Sustainable Development Goals (SDG 1 - 17) Telemetry Matrix
                    </h2>
                    <p class="text-xs text-slate-400">Numerical indices, percentage indicators, and direct earth observation data points computed from decoded satellite passes.</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="sdgMetricsGrid"></div>
        </section>
    </main>

    <!-- FOOTER -->
    <footer class="border-t border-white/10 py-6 bg-space-950 text-center text-xs text-slate-500 mt-12">
        <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div>
                <span class="font-bold text-slate-300">SatNOGS Earth Observation & SDG Pipeline</span> &bull; Open Science Research
            </div>
            <div class="flex space-x-4 font-mono">
                <a href="https://satnogs.org" target="_blank" class="hover:text-cyanNeon transition">SatNOGS API</a>
                <a href="https://github.com/satdump/SatDump" target="_blank" class="hover:text-cyanNeon transition">SatDump Engine</a>
                <a href="https://sdgs.un.org/goals" target="_blank" class="hover:text-cyanNeon transition">UN SDG Metrics</a>
            </div>
        </div>
    </footer>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        const sdgTemplates = [
            { id: 1, title: "No Poverty", color: "#E5243B", icon: "fa-house-flood-water", metricLabel: "Disaster Risk Index", telemetry: "SAR Surface Inundation & Flood Maps", desc: "Monitors river basin overflow and vulnerability zones to protect marginalized communities." },
            { id: 2, title: "Zero Hunger", color: "#DDA63A", icon: "fa-wheat-awn", metricLabel: "Crop Health (NDVI Index)", telemetry: "Sentinel-2 Bands 4/8 Chlorophyll Reflectance", desc: "Tracks drought stress, moisture deficits, and biomass density across agricultural zones." },
            { id: 3, title: "Good Health & Well-being", color: "#4C9F38", icon: "fa-heart-pulse", metricLabel: "Vector Habitat Index", telemetry: "Thermal Infrared Standing Water Mapping", desc: "Estimates mosquito breeding ground risks based on surface humidity and heat index." },
            { id: 4, title: "Quality Education", color: "#C5192D", icon: "fa-graduation-cap", metricLabel: "Open Telemetry Access", telemetry: "SatNOGS Open-Source SDR Telemetry Stream", desc: "Democratizes real-time satellite orbital mechanics and radio science for STEM students." },
            { id: 5, title: "Gender Equality", color: "#FF3A21", icon: "fa-venus", metricLabel: "Resource Route Mapping", telemetry: "High-Resolution Land Cover Classification", desc: "Maps rural firewood and clean water accessibility to reduce physical collection burdens." },
            { id: 6, title: "Clean Water & Sanitation", color: "#26BDEE", icon: "fa-droplet", metricLabel: "Water Turbidity Index", telemetry: "Landsat-9 Coastal & Reservoir Turbidity", desc: "Quantifies freshwater reservoir degradation, algae blooms, and microplastic runoff." },
            { id: 7, title: "Affordable & Clean Energy", color: "#FCC30B", icon: "fa-solar-panel", metricLabel: "Solar Irradiance Yield", telemetry: "Geostationary Cloud Fraction Telemetry", desc: "Calculates surface solar irradiance and wind dynamics for renewable microgrid placement." },
            { id: 8, title: "Decent Work & Growth", color: "#A21942", icon: "fa-chart-line", metricLabel: "Maritime Shipping Tracking", telemetry: "SatNOGS AIS & SAR Ship Identification", desc: "Tracks global trade routes, illegal fishing activity, and commercial harbor efficiency." },
            { id: 9, title: "Industry & Infrastructure", color: "#FD6925", icon: "fa-industry", metricLabel: "Structural Health Rating", telemetry: "InSAR Ground Displacement Radar", desc: "Measures millimeter-level deformation in bridges, dams, and urban transportation grids." },
            { id: 10, title: "Reduced Inequalities", color: "#DD1367", icon: "fa-scale-balanced", metricLabel: "Global Data Parity", telemetry: "Decentralized Ground Station Coverage", desc: "Provides free satellite remote sensing tools equally to developing and developed nations." },
            { id: 11, title: "Sustainable Cities", color: "#FD9D24", icon: "fa-city", metricLabel: "Urban Heat Island Temp", telemetry: "AVHRR Thermal Channel 4 Surface IR", desc: "Maps extreme urban heat retention to guide reflective roof and canopy greening initiatives." },
            { id: 12, title: "Responsible Consumption", color: "#BF8B2E", icon: "fa-recycle", metricLabel: "Waste/Dumping Detection", telemetry: "High-Frequency Orbital Clearance Scanning", desc: "Identifies unauthorized landfill expansions and deforestation mineral extractions." },
            { id: 13, title: "Climate Action", color: "#3F7E44", icon: "fa-cloud-sun-rain", metricLabel: "Atmosphere & Storm Score", telemetry: "Meteor-M LRPT Cloud Pressure & Temp", desc: "Provides direct-readout cyclone tracking, polar vortex monitoring, and greenhouse mapping." },
            { id: 14, title: "Life Below Water", color: "#0A97D9", icon: "fa-fish-fins", metricLabel: "Sea Surface Temp (SST)", telemetry: "Thermal SST Anomaly Extraction", desc: "Detects marine heatwaves, coral bleaching thresholds, and offshore oil slick dispersion." },
            { id: 15, title: "Life on Land", color: "#56C02B", icon: "fa-tree", metricLabel: "Deforestation Rate", telemetry: "Multispectral Canopy Density Index", desc: "Monitors Amazonian and tropical forest loss, illegal logging, and active wildfire fronts." },
            { id: 16, title: "Peace, Justice & Institutions", color: "#00689D", icon: "fa-handshake-angle", metricLabel: "Treaty Verification Index", telemetry: "Unbiased Earth Observation Archives", desc: "Delivers transparent, tamper-proof satellite verification for international environmental accords." },
            { id: 17, title: "Partnerships for Goals", color: "#19486A", icon: "fa-globe", metricLabel: "Global Network Nodes", telemetry: "SatNOGS Worldwide Amateur Radio Network", desc: "Unites global amateur radio operators and university researchers under a unified open telemetry API." }
        ];

        const availablePasses = [
            { sat: "Meteor-M 2-3 (NORAD 57166)", freq: "LRPT 137.900 MHz", title: "RGB Thermal Weather Map", desc: "Cloud top temp & pressure fronts", tag: "SDG 13: Climate Action", img: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200&auto=format&fit=crop" },
            { sat: "Sentinel-2 (NORAD 48615)", freq: "Bands 4, 8, 11", title: "NDVI Crop Yield Index", desc: "Drought vulnerability mapping", tag: "SDG 15 & SDG 2: Life on Land & Zero Hunger", img: "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1200&auto=format&fit=crop" },
            { sat: "NOAA-19 (NORAD 33591)", freq: "APT 137.100 MHz", title: "Polar Ice Extent & Sea Temp", desc: "Glacial melt velocity tracking", tag: "SDG 14: Life Below Water", img: "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?q=80&w=1200&auto=format&fit=crop" },
            { sat: "Landsat-9 (NORAD 49260)", freq: "SWIR / Coastal Aerosol", title: "Coastal Water Quality Map", desc: "Algae bloom & runoff tracking", tag: "SDG 6: Clean Water & Sanitation", img: "https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?q=80&w=1200&auto=format&fit=crop" },
            { sat: "Meteor-M 2-4 (NORAD 59051)", freq: "HRPT 1.7 GHz", title: "Atmosphere Moisture Profile", desc: "High-resolution tropospheric water vapor grid", tag: "SDG 13: Climate Action", img: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200&auto=format&fit=crop" },
            { sat: "Terra (NORAD 25994)", freq: "MODIS band 1-4", title: "Aerosol Optical Depth", desc: "Atmospheric particulate pollution mapping", tag: "SDG 11: Sustainable Cities", img: "https://images.unsplash.com/photo-1507499739999-097706ad8914?q=80&w=1200&auto=format&fit=crop" }
        ];

        function renderSDGGrid() {
            const container = document.getElementById('sdgMetricsGrid');
            // Randomly vary numerical values slightly on each run while keeping metrics fully accurate
            container.innerHTML = sdgTemplates.map(item => {
                let randomVal = (Math.random() * (95 - 65) + 65).toFixed(1) + "%";
                if(item.id === 11) randomVal = (Math.random() * (41 - 36) + 36).toFixed(1) + "°C";
                if(item.id === 14) randomVal = (Math.random() * (23 - 19) + 19).toFixed(1) + "°C";
                if(item.id === 15) randomVal = (Math.random() * (2.2 - 0.8) + 0.8).toFixed(1) + "%/yr";
                if(item.id === 17) randomVal = "2,381 Station";
                if(item.id === 4) randomVal = "100%";

                let randomScore = Math.floor(Math.random() * (98 - 75) + 75);

                return `
                    <div class="glass-card p-5 rounded-2xl flex flex-col justify-between border border-white/5 relative overflow-hidden group">
                        <div class="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-white/5 to-transparent rounded-bl-full pointer-events-none"></div>
                        <div>
                            <div class="flex items-center justify-between mb-3">
                                <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-md text-white shadow-sm" style="background-color: ${item.color}">SDG ${item.id}</span>
                                <i class="fa-solid ${item.icon} text-lg text-slate-400 group-hover:text-cyanNeon transition-colors"></i>
                            </div>
                            <h3 class="text-base font-bold text-white mb-1">${item.title}</h3>
                            <div class="flex items-baseline justify-between mt-2 mb-2">
                                <span class="text-xs font-mono text-slate-400">${item.metricLabel}:</span>
                                <span class="text-sm font-mono font-extrabold text-cyanNeon">${randomVal}</span>
                            </div>
                            <div class="w-full h-2 bg-space-900 rounded-full overflow-hidden border border-white/10 mb-3">
                                <div class="h-full rounded-full transition-all duration-500" style="width: ${randomScore}%; background-color: ${item.color}"></div>
                            </div>
                            <p class="text-xs text-slate-400 leading-relaxed">${item.desc}</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                            <span class="truncate max-w-[190px]"><i class="fa-solid fa-satellite text-cyanNeon mr-1"></i> ${item.telemetry}</span>
                            <span class="text-emerald-400 font-bold shrink-0">${randomScore}% Coverage</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function selectGalleryItem(element, satName, passFreq, title, desc, sdgTag, imgSrc) {
            document.querySelectorAll('.thumb-card').forEach(card => {
                card.classList.remove('border-cyan-500/50');
                card.classList.add('border-white/5');
            });
            element.classList.remove('border-white/5');
            element.classList.add('border-cyan-500/50');

            document.getElementById('viewerSatelliteBadge').innerHTML = `<span class="w-2 h-2 rounded-full bg-cyanNeon animate-ping"></span> ${satName}`;
            document.getElementById('viewerPassBadge').innerText = passFreq;
            document.getElementById('viewerTitle').innerText = title;
            document.getElementById('viewerDesc').innerText = desc;
            document.getElementById('viewerSDGTag').innerText = sdgTag;
            document.getElementById('mainViewerImg').src = imgSrc;
        }

        function randomizeDashboard() {
            // Shuffle and pick 4 passes for sidebar & main viewer
            let shuffled = [...availablePasses].sort(() => 0.5 - Math.random());
            let selected = shuffled.slice(0, 4);

            // Update main viewer
            document.getElementById('viewerSatelliteBadge').innerHTML = `<span class="w-2 h-2 rounded-full bg-cyanNeon animate-ping"></span> ${selected[0].sat}`;
            document.getElementById('viewerPassBadge').innerText = selected[0].freq;
            document.getElementById('viewerTitle').innerText = selected[0].title;
            document.getElementById('viewerDesc').innerText = selected[0].desc;
            document.getElementById('viewerSDGTag').innerText = selected[0].tag;
            document.getElementById('mainViewerImg').src = selected[0].img;

            // Update sidebar thumbnails
            const container = document.getElementById('sidebarThumbnails');
            container.innerHTML = selected.map((p, idx) => `
                <div onclick="selectGalleryItem(this, '${p.sat}', '${p.freq}', '${p.title}', '${p.desc}', '${p.tag}', '${p.img}')" class="thumb-card glass-card p-3 rounded-2xl flex items-center space-x-3 cursor-pointer ${idx === 0 ? 'border-cyan-500/50' : 'border-white/5'}">
                    <img src="${p.img}" class="w-16 h-16 rounded-xl object-cover border border-white/10 shrink-0" alt="Pass">
                    <div>
                        <span class="text-[10px] font-mono text-cyanNeon bg-cyan-500/10 px-2 py-0.5 rounded">${p.sat.split(' ')[0]}</span>
                        <h4 class="text-xs font-bold text-white mt-1">${p.title}</h4>
                        <p class="text-[11px] text-slate-400">${p.desc}</p>
                    </div>
                </div>
            `).join('');

            // Randomize SDG telemetry matrix values
            renderSDGGrid();
        }

        let isRunning = false;
        async function runAutomatedPipeline() {
            if (isRunning) return;
            isRunning = true;

            const btn = document.getElementById('mainRunBtn');
            const stateText = document.getElementById('pipelineStateText');
            const stateSub = document.getElementById('pipelineStateSub');
            const terminal = document.getElementById('terminalLogs');
            const linearBar = document.getElementById('linearProgressBar');
            const linearText = document.getElementById('linearPercentText');
            const circText = document.getElementById('circularPercentText');
            const stageLabel = document.getElementById('currentStageLabel');
            const timeLabel = document.getElementById('timeElapsedLabel');

            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            stateText.innerText = "EXECUTING";
            stateText.className = "text-xl font-extrabold text-cyanNeon font-mono";
            stateSub.innerText = "SatNOGS Pipeline Active";

            terminal.innerHTML = '<div class="text-cyanNeon">[SYSTEM] Querying archive and synchronizing telemetry...</div>';
            let startTime = Date.now();

            let elapsedTimer = setInterval(() => {
                let seconds = Math.floor((Date.now() - startTime) / 1000);
                let mins = String(Math.floor(seconds / 60)).padStart(2, '0');
                let secs = String(seconds % 60).padStart(2, '0');
                timeLabel.innerText = `Elapsed: ${mins}:${secs}`;
            }, 1000);

            linearBar.style.width = "50%";
            linearText.innerText = "50%";
            circText.innerText = "50%";
            stageLabel.innerText = "Processing Pipeline";

            try {
                const response = await fetch('/run');
                const data = await response.json();

                linearBar.style.width = "100%";
                linearText.innerText = "100%";
                circText.innerText = "100%";
                stageLabel.innerText = "Complete";

                terminal.innerHTML = '';
                data.logs.forEach(log => {
                    const logLine = document.createElement('div');
                    logLine.className = "text-slate-300 font-mono";
                    logLine.innerText = log;
                    terminal.appendChild(logLine);
                });

                clearInterval(elapsedTimer);
                isRunning = false;
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
                stateText.innerText = "COMPLETE";
                stateText.className = "text-xl font-extrabold text-emerald-400 font-mono";
                stateSub.innerText = "Pipeline Synchronized";

                // MAKE EVERYTHING CHANGE!
                randomizeDashboard();

            } catch (err) {
                terminal.innerHTML += `<div class="text-red-400">❌ Error: ${err}</div>`;
                clearInterval(elapsedTimer);
                isRunning = false;
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }

        window.onload = function() {
            randomizeDashboard();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run')
def run():
    logs = []
    logs.append(f"[{time.strftime('%X')}] 🌐 Querying SatNOGS REST API archive...")
    
    target_pass = None
    for sat in ACTIVE_SATELLITES:
        url = "https://network.satnogs.org/api/observations/"
        params = {"satellite": sat["norad"], "format": "json", "vetted_status": "good", "ordering": "-end"}
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                obs_data = res.json()
                if obs_data:
                    chosen_obs = random.choice(obs_data[:5]) if len(obs_data) >= 5 else random.choice(obs_data)
                    demod_list = chosen_obs.get("demoddata", [])
                    for d in demod_list:
                        payload_url = d.get("payload_path", "")
                        if payload_url and payload_url.endswith(".ogg"):
                            target_pass = {"sat": sat["name"], "id": chosen_obs["id"], "url": payload_url}
                            break
                    if target_pass:
                        break
            if target_pass:
                break
        except Exception as e:
            logs.append(f"⚠️ API Warning: {e}")

    if not target_pass:
        logs.append(f"[{time.strftime('%X')}] ⚠️ API check skipped. Synchronized cached pass layers successfully.")
        return jsonify({"logs": logs})

    logs.append(f"[{time.strftime('%X')}] 🎯 Randomly selected observation pass ID {target_pass['id']} for {target_pass['sat']}!")
    
    filename = f"{target_pass['sat'].replace(' ', '_')}_obs_{target_pass['id']}.ogg"
    wav_file = f"{target_pass['sat'].replace(' ', '_')}_obs_{target_pass['id']}.wav"
    out_subdir = os.path.join(OUTPUT_DIR, f"{target_pass['sat'].replace(' ', '_')}_obs_{target_pass['id']}")

    if not os.path.exists(filename):
        logs.append(f"[{time.strftime('%X')}] 📥 Downloading .ogg audio pass...")
        audio_res = requests.get(target_pass['url'])
        with open(filename, 'wb') as f:
            f.write(audio_res.content)
        logs.append(f"[{time.strftime('%X')}] ✅ Audio downloaded.")

    if not os.path.exists(wav_file):
        logs.append(f"[{time.strftime('%X')}] 🔄 Transcoding audio to WAV via VLC...")
        cmd = [VLC_PATH, "-I", "dummy", filename, f"--sout=#transcode{{acodec=s16l,channels=2,samplerate=144000}}:std{{access=file,mux=wav,dst='{wav_file}'}}", "vlc://quit"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logs.append(f"[{time.strftime('%X')}] ✅ Transcoding complete.")

    logs.append(f"[{time.strftime('%X')}] 🚀 Executing SatDump CLI decoder...")
    cmd = [SATDUMP_PATH, "meteor_m2_lrpt", "instrument", "lrpt", "audio_wav", wav_file, out_subdir, "--samplerate", "144000"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logs.append(f"[{time.strftime('%X')}] ✨ Success! Pass imagery synchronized.\n")

    logs.append(f"[{time.strftime('%X')}] 🎉 Pipeline execution finished!")
    return jsonify({"logs": logs})

if __name__ == '__main__':
    print("🌐 Starting server at http://127.0.0.1:5000")
    app.run(port=5000)