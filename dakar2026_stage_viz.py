#!/usr/bin/env python3
"""
Dakar Rally Live Timing Server v8
- Uses actual class IDs from API data (team.clazz) for filtering
- Class-relative position calculations based on real class membership
- Simplified sorting (always P1 to last)
- 15 second countdown timer
- Driver photos

Usage:
    pip install flask requests
    python dakar_server.py
    
Then open http://localhost:5000 in your browser
"""

from flask import Flask, jsonify, request, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

API_BASE = "https://www.dakar.live.worldrallyraidchampionship.com/api"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dakar Rally 2026 - Live Timing</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #dc2626; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .countdown-ring { transform: rotate(-90deg); }
        .countdown-ring circle { transition: stroke-dashoffset 1s linear; }
        .driver-photo { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #e5e7eb; }
        .wp-cell { min-width: 80px; font-size: 0.75rem; }
        .table-scroll { overflow-x: auto; }
        .sticky-col { position: sticky; left: 0; background: inherit; z-index: 10; min-width: 280px; }
        .pos-1 { background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%); }
        .pos-2 { background: linear-gradient(135deg, #f3f4f6 0%, #d1d5db 100%); }
        .pos-3 { background: linear-gradient(135deg, #fed7aa 0%, #fb923c 100%); }
        .class-btn { transition: all 0.2s; }
        .class-btn:hover { transform: translateY(-1px); }
        .class-btn.active { box-shadow: 0 0 0 2px white, 0 0 0 4px currentColor; }
        .sortable { cursor: pointer; user-select: none; }
        .sortable:hover { background: rgba(255,255,255,0.1); }
        .sort-indicator { display: inline-block; margin-left: 4px; opacity: 0.3; }
        .sort-indicator.active { opacity: 1; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div id="app">
        <!-- Header -->
        <div class="bg-gradient-to-r from-red-600 to-red-800 text-white px-3 py-2 shadow-lg">
            <div class="max-w-full mx-auto flex items-center justify-between flex-wrap gap-2">
                <!-- Title + Categories -->
                <div class="flex items-center gap-4 flex-wrap">
                    <div class="flex items-center gap-2">
                        <span class="text-xl">🏆</span>
                        <h1 class="text-lg font-bold">Dakar 2026</h1>
                    </div>

                    <!-- Category Tabs inline -->
                    <div class="flex gap-1" id="category-tabs">
                        <button onclick="setCategory('M')" id="cat-M" class="class-btn px-2 py-1 rounded bg-white/20 hover:bg-white/30 text-sm font-medium">🏍️ Bikes</button>
                        <button onclick="setCategory('A')" id="cat-A" class="class-btn px-2 py-1 rounded bg-white/20 hover:bg-white/30 text-sm font-medium active">🚗 Cars</button>
                        <button onclick="setCategory('K')" id="cat-K" class="class-btn px-2 py-1 rounded bg-white/20 hover:bg-white/30 text-sm font-medium">🏛️ Classic</button>
                        <button onclick="setCategory('F')" id="cat-F" class="class-btn px-2 py-1 rounded bg-white/20 hover:bg-white/30 text-sm font-medium">🔋 M1000</button>
                    </div>

                    <!-- Sub-class filters inline -->
                    <div class="flex gap-1" id="class-filters"></div>
                </div>

                <!-- Controls -->
                <div class="flex items-center gap-2">
                    <select id="stage" onchange="fetchData()" class="bg-white/20 border border-white/30 rounded px-2 py-1 text-sm text-white">
                        <option value="0" selected class="text-gray-800">Prologue</option>
                        <option value="1" class="text-gray-800">S1</option>
                        <option value="2" class="text-gray-800">S2</option>
                        <option value="3" class="text-gray-800">S3</option>
                        <option value="4" class="text-gray-800">S4</option>
                        <option value="5" class="text-gray-800">S5</option>
                        <option value="6" class="text-gray-800">S6</option>
                        <option value="7" class="text-gray-800">S7</option>
                        <option value="8" class="text-gray-800">S8</option>
                        <option value="9" class="text-gray-800">S9</option>
                        <option value="10" class="text-gray-800">S10</option>
                        <option value="11" class="text-gray-800">S11</option>
                        <option value="12" class="text-gray-800">S12</option>
                        <option value="13" class="text-gray-800">S13</option>
                    </select>

                    <!-- Compact Countdown -->
                    <div class="flex items-center gap-1 bg-white/20 rounded px-2 py-1">
                        <svg class="countdown-ring" width="20" height="20">
                            <circle cx="10" cy="10" r="8" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
                            <circle id="countdown-circle" cx="10" cy="10" r="8" fill="none" stroke="white" stroke-width="2"
                                stroke-dasharray="50" stroke-dashoffset="0" stroke-linecap="round"/>
                        </svg>
                        <span id="countdown-text" class="text-sm font-mono font-bold">15</span>
                    </div>

                    <button onclick="fetchData()" class="bg-white/20 hover:bg-white/30 border border-white/30 rounded px-2 py-1 text-sm">
                        <span id="refresh-icon">🔄</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Stats Bar -->
        <div class="bg-white border-b shadow-sm">
            <div class="max-w-full mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-4">
                <div class="flex items-center gap-6 text-sm" id="stats">
                    <span class="text-gray-500">Loading...</span>
                </div>
                <div class="flex items-center gap-4">
                    <div id="sort-info" class="text-xs text-gray-500"></div>
                    <div id="live-indicator" class="hidden flex items-center gap-2">
                        <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                        <span class="text-green-600 text-sm font-medium">LIVE</span>
                    </div>
                    <div class="text-xs text-gray-500" id="lastUpdate"></div>
                    <div id="loading-indicator" class="hidden">
                        <div class="loader"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="max-w-full mx-auto p-4">
            <div id="content" class="bg-white rounded-lg shadow overflow-hidden">
                <div class="p-12 text-center">
                    <div class="loader mx-auto" style="width:48px;height:48px;border-width:4px;"></div>
                    <p class="mt-4 text-gray-500">Loading live timing data...</p>
                </div>
            </div>
        </div>

        <!-- Legend -->
        <div class="max-w-full mx-auto px-4 pb-4">
            <div class="bg-white rounded-lg shadow p-4 text-sm text-gray-600">
                <div class="font-semibold mb-2">Legend:</div>
                <div class="flex flex-wrap gap-6">
                    <div><span class="font-mono bg-gray-100 px-1 rounded">WP1, WP2...</span> = Waypoint stage times (click to sort)</div>
                    <div><span class="font-mono bg-blue-100 text-blue-800 px-1 rounded">Stage</span> = Stage position within selected class</div>
                    <div><span class="font-mono bg-green-100 text-green-800 px-1 rounded">Rally</span> = Overall position within selected class</div>
                    <div><span class="bg-amber-500 text-white text-xs px-1 rounded">W2RC</span> = World Rally-Raid Championship</div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center py-6 text-gray-500 text-sm">
            Data from World Rally-Raid Championship API • Auto-refreshes every 15 seconds • Click column headers to sort
        </div>
    </div>

    <script>
        let countdownInterval = null;
        let countdown = 15;
        let allWaypoints = [];
        let currentCategory = 'A';
        let currentClass = 'all';
        let rawData = [];
        let processedData = [];
        let sortColumn = 'classStagePos';
        let stageComparisonWp = null;
        
        const FLAGS = {
            fra: '🇫🇷', esp: '🇪🇸', ger: '🇩🇪', GER: '🇩🇪', aus: '🇦🇺', arg: '🇦🇷',
            qat: '🇶🇦', ksa: '🇸🇦', KSA: '🇸🇦', bel: '🇧🇪', por: '🇵🇹', POR: '🇵🇹', ned: '🇳🇱', NED: '🇳🇱',
            cze: '🇨🇿', pol: '🇵🇱', bra: '🇧🇷', jpn: '🇯🇵', chn: '🇨🇳',
            rsa: '🇿🇦', RSA: '🇿🇦', aut: '🇦🇹', chi: '🇨🇱', CHI: '🇨🇱', ltu: '🇱🇹', nzl: '🇳🇿',
            usa: '🇺🇸', gbr: '🇬🇧', ita: '🇮🇹', mex: '🇲🇽', lux: '🇱🇺',
            ecu: '🇪🇨', kaz: '🇰🇿', ang: '🇦🇴', ANG: '🇦🇴', moz: '🇲🇿', rou: '🇷🇴',
            sui: '🇨🇭', SUI: '🇨🇭', svk: '🇸🇰', svn: '🇸🇮', ukr: '🇺🇦', ind: '🇮🇳',
            sau: '🇸🇦', SAU: '🇸🇦', uae: '🇦🇪', UAE: '🇦🇪', bhr: '🇧🇭', kwt: '🇰🇼',
            col: '🇨🇴', per: '🇵🇪', ury: '🇺🇾', crc: '🇨🇷', rus: '🇷🇺',
        };
        
        // Map actual class IDs from API to class names
        // These are the real class IDs from team.clazz field
        const CLASS_ID_MAP = {
            // Cars (A) - Ultimate/T1+
            'e18df6479eeb221edf506539ca01a0fb': 'ultimate',
            'cd3a224fa3f90b3d44ad779de5a61de0': 'ultimate',
            '56b1895a94e9bde92261fefdccfd9300': 'ultimate',
            '8ec12cac9b3eb552e37a6f52f3eb874c': 'ultimate',
            // Cars (A) - T3 Lightweight
            '75ca283e010c2d8f55515206c945cc5b': 't3',
            // Cars (A) - SSV
            '21a677c34d3929cb01e5e7163a1dda0c': 'ssv',
            'fa9bd58337b8e5a6c01aea95af09dda7': 'ssv',
            // Cars (A) - Stock/T2
            'f92c26257b0bc1bf01d1ed3406a2798e': 'stock',
            '25ab9f4ea3d9f41969b2b47f627168aa': 'stock',
            // Cars (A) - Trucks
            '596e4eb3814731d718603e5313878fd2': 'trucks',
            '0aca7403b23b1d4308e5e124290e09bc': 'trucks',
            // Bikes (M) - RallyGP (top factory riders)
            'bb94ac9163db104dfb3b5f878235edb9': 'rallygp',
            // Bikes (M) - Rally2 (larger field)
            '978032dc39dd0c9245c7bc4097a72ac0': 'rally2',
        };

        // Track unknown class IDs for debugging
        const unknownClassIds = new Set();
        
        // Get the class name from class ID
        function getClassName(clazzId) {
            if (!clazzId) return 'unknown';
            if (CLASS_ID_MAP[clazzId]) return CLASS_ID_MAP[clazzId];
            // Log unknown class IDs to console for debugging
            if (!unknownClassIds.has(clazzId)) {
                unknownClassIds.add(clazzId);
                console.log('Unknown class ID:', clazzId, '- add to CLASS_ID_MAP');
            }
            return 'unknown';
        }
        
        const CLASS_CONFIG = {
            'A': {
                name: 'Cars (Auto)',
                icon: '🚗',
                liveDisplay: true,
                classes: {
                    'all': { name: 'All Cars', icon: '🚗' },
                    'ultimate': { name: 'Ultimate', icon: '🏆' },
                    't3': { name: 'T3 Lightweight', icon: '🚙' },
                    'ssv': { name: 'SSV', icon: '🏎️' },
                    'stock': { name: 'Stock', icon: '🚙' },
                    'trucks': { name: 'Trucks', icon: '🚛' },
                }
            },
            'M': {
                name: 'Bikes (Moto)',
                icon: '🏍️',
                liveDisplay: true,
                classes: {
                    'all': { name: 'All Bikes', icon: '🏍️' },
                    'rallygp': { name: 'RallyGP', icon: '🏆' },
                    'rally2': { name: 'Rally2', icon: '🏍️' },
                    'original': { name: 'Original by Motul', icon: '🛡️' },
                }
            },
            'K': {
                name: 'Classic',
                icon: '🏛️',
                liveDisplay: false,
                classes: {
                    'all': { name: 'All Classic', icon: '🏛️' },
                }
            },
            'F': {
                name: 'Future Mission 1000',
                icon: '🔋',
                liveDisplay: false,
                classes: {
                    'all': { name: 'All Future', icon: '🔋' },
                }
            }
        };

        function getFlag(nat) { 
            if (!nat) return '🏁';
            return FLAGS[nat.toLowerCase()] || FLAGS[nat] || '🏁'; 
        }

        function formatTime(ms) {
            if (!ms) return '-';
            const secs = Math.floor(ms / 1000);
            const h = Math.floor(secs / 3600);
            const m = Math.floor((secs % 3600) / 60);
            const s = secs % 60;
            if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
            return `${m}:${s.toString().padStart(2,'0')}`;
        }

        function formatGap(ms) {
            if (!ms || ms === 0) return '-';
            const prefix = ms > 0 ? '+' : '-';
            return prefix + formatTime(Math.abs(ms));
        }

        function getDriverName(competitors) {
            if (!competitors || !competitors.length) return 'Unknown';
            const driver = competitors.find(c => c.role === 'P') || competitors[0];
            return driver.name || `${driver.firstName} ${driver.lastName}`;
        }
        
        function getDriverPhoto(competitors) {
            if (!competitors || !competitors.length) return null;
            const driver = competitors.find(c => c.role === 'P') || competitors[0];
            return driver.profil_sm || driver.profil || null;
        }

        function updateCountdown() {
            countdown--;
            if (countdown <= 0) {
                countdown = 15;
                fetchData();
            }
            document.getElementById('countdown-text').textContent = countdown;
            const circle = document.getElementById('countdown-circle');
            const offset = 50 - (50 * countdown / 15);
            circle.style.strokeDashoffset = offset;
        }

        function startCountdown() {
            if (countdownInterval) clearInterval(countdownInterval);
            countdown = 15;
            document.getElementById('countdown-text').textContent = countdown;
            document.getElementById('countdown-circle').style.strokeDashoffset = 0;
            countdownInterval = setInterval(updateCountdown, 1000);
        }
        
        function setCategory(cat) {
            currentCategory = cat;
            currentClass = 'all';
            sortColumn = 'classStagePos';
            
            document.querySelectorAll('#category-tabs button').forEach(btn => {
                btn.classList.remove('active', 'bg-white/40');
                btn.classList.add('bg-white/20');
            });
            document.getElementById('cat-' + cat).classList.add('active', 'bg-white/40');
            document.getElementById('cat-' + cat).classList.remove('bg-white/20');
            
            updateClassFilters();
            
            const liveIndicator = document.getElementById('live-indicator');
            if (CLASS_CONFIG[cat].liveDisplay) {
                liveIndicator.classList.remove('hidden');
            } else {
                liveIndicator.classList.add('hidden');
            }
            
            fetchData();
        }
        
        function setClass(cls) {
            currentClass = cls;

            document.querySelectorAll('#class-filters button').forEach(btn => {
                btn.classList.remove('active', 'bg-amber-500', 'text-white');
                btn.classList.add('bg-white/80', 'text-gray-700');
            });
            const activeBtn = document.querySelector(`#class-filters button[data-class="${cls}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active', 'bg-amber-500', 'text-white');
                activeBtn.classList.remove('bg-white/80', 'text-gray-700');
            }

            if (rawData.length > 0) {
                processedData = processData(rawData);
                sortAndRender();
            }
        }
        
        function updateClassFilters() {
            const container = document.getElementById('class-filters');
            const config = CLASS_CONFIG[currentCategory];

            let html = '';
            for (const [key, cls] of Object.entries(config.classes)) {
                const isActive = key === currentClass;
                const activeClass = isActive ? 'bg-amber-500 text-white' : 'bg-white/80 text-gray-700 hover:bg-white';
                html += `<button onclick="setClass('${key}')" data-class="${key}"
                    class="class-btn px-2 py-1 rounded text-xs font-medium ${activeClass}">
                    ${cls.icon} ${cls.name}
                </button>`;
            }
            container.innerHTML = html;
        }
        
        function sortBy(column) {
            sortColumn = column;
            sortAndRender();
        }
        
        function sortAndRender() {
            const sorted = [...processedData].sort((a, b) => {
                let aVal, bVal;
                
                if (sortColumn === 'classStagePos') {
                    aVal = a.classStagePos || 9999;
                    bVal = b.classStagePos || 9999;
                } else if (sortColumn === 'classOverallPos') {
                    aVal = a.classOverallPos || 9999;
                    bVal = b.classOverallPos || 9999;
                } else if (sortColumn === 'startPos') {
                    aVal = a.startPos || 9999;
                    bVal = b.startPos || 9999;
                } else if (sortColumn === 'bib') {
                    aVal = a.bib || 9999;
                    bVal = b.bib || 9999;
                } else if (sortColumn.startsWith('wp_')) {
                    const wp = sortColumn.replace('wp_', '');
                    aVal = a.waypointData[wp]?.classPos || 9999;
                    bVal = b.waypointData[wp]?.classPos || 9999;
                } else {
                    aVal = 0;
                    bVal = 0;
                }
                
                return aVal - bVal;
            });
            
            renderTable(sorted);
            
            const colNames = {
                'classStagePos': 'Stage Position',
                'classOverallPos': 'Rally Position',
                'startPos': 'Start Position',
                'bib': 'Bib Number'
            };
            let colName = colNames[sortColumn] || sortColumn.replace('wp_', 'WP ');
            document.getElementById('sort-info').textContent = `Sorted by: ${colName}`;
        }

        function processData(data) {
            rawData = data;
            
            const wpSet = new Set();
            data.forEach(entry => {
                const cs = entry.cs || {};
                Object.keys(cs).forEach(wp => {
                    if (!wp.includes('penality') && !wp.includes('ASS') && !wp.includes('PASS')) {
                        wpSet.add(wp);
                    }
                });
            });
            allWaypoints = Array.from(wpSet).sort();
            
            // First pass: extract raw data
            let entries = data.map(entry => {
                const team = entry.team || {};
                const dss = entry.dss || {};
                const cg = entry.cg || {};
                const cs = entry.cs || {};
                const ce = entry.ce || {};
                
                // Get the actual class name from the class ID
                const clazzId = team.clazz;
                const clazzName = getClassName(clazzId);
                
                const waypointData = {};
                allWaypoints.forEach(wp => {
                    if (cs[wp] || cg[wp]) {
                        waypointData[wp] = {
                            stageTime: cs[wp]?.absolute?.[0],
                            overallTime: cg[wp]?.absolute?.[0],
                        };
                    }
                });
                
                const wpKeys = Object.keys(cs).filter(k => !k.includes('penality'));
                const latestWp = wpKeys.length ? wpKeys.sort().pop() : null;
                const latestStageData = latestWp ? cs[latestWp] : null;
                
                const cgKeys = Object.keys(cg).filter(k => !k.includes('penality'));
                const latestCgWp = cgKeys.length ? cgKeys.sort().pop() : null;
                const latestOverallData = latestCgWp ? cg[latestCgWp] : null;
                
                return {
                    bib: team.bib,
                    brand: team.brand,
                    model: team.model,
                    vehicle: team.vehicle,
                    clazzId: clazzId,
                    clazzName: clazzName,  // Use actual class from API
                    driver: getDriverName(team.competitors),
                    driverPhoto: getDriverPhoto(team.competitors),
                    nationality: team.competitors?.[0]?.nationality,
                    isW2RC: team.is?.w2rc,
                    isOBM: team.is?.obm,  // Original by Motul flag
                    startPos: dss.position,
                    hasStarted: dss.real,
                    waypointData: waypointData,
                    latestStageTime: latestStageData?.absolute?.[0],
                    latestOverallTime: latestOverallData?.absolute?.[0],
                };
            });

            // Filter by actual class (using clazzName from API) or by OBM flag
            if (currentClass !== 'all') {
                if (currentClass === 'original') {
                    // Original by Motul is a flag, not a class
                    entries = entries.filter(e => e.isOBM);
                } else {
                    entries = entries.filter(e => e.clazzName === currentClass);
                }
            }
            
            // Calculate class-relative positions for STAGE at furthest reached waypoint
            // Find the furthest waypoint that ANY entry has reached (last in sorted allWaypoints that has data)
            let furthestReachedWp = null;

            for (const wp of allWaypoints) {
                const anyHaveThisWp = entries.some(e => e.waypointData[wp]?.stageTime);
                if (anyHaveThisWp) {
                    furthestReachedWp = wp;
                }
            }

            // Store the comparison waypoint globally for display
            stageComparisonWp = furthestReachedWp;

            // Calculate positions based on furthest reached waypoint
            // Only rank drivers who have reached that waypoint, by their time there
            if (furthestReachedWp) {
                const stageRanked = [...entries]
                    .filter(e => e.waypointData[furthestReachedWp]?.stageTime)
                    .sort((a, b) => a.waypointData[furthestReachedWp].stageTime - b.waypointData[furthestReachedWp].stageTime);

                const stageLeaderTime = stageRanked[0]?.waypointData[furthestReachedWp]?.stageTime || 0;

                stageRanked.forEach((entry, idx) => {
                    entry.classStagePos = idx + 1;
                    entry.classStageGap = entry.waypointData[furthestReachedWp].stageTime - stageLeaderTime;
                    entry.stageWaypoint = furthestReachedWp;
                });

                // Drivers who haven't reached the furthest waypoint yet get no position
                entries.filter(e => !e.waypointData[furthestReachedWp]?.stageTime).forEach(e => {
                    e.classStagePos = null;
                    e.classStageGap = null;
                    e.stageWaypoint = null;
                });
            } else {
                // No waypoint data at all
                entries.forEach(e => {
                    e.classStagePos = null;
                    e.classStageGap = null;
                    e.stageWaypoint = null;
                });
            }
            
            // Calculate class-relative positions for OVERALL RALLY at the same waypoint as stage
            // This ensures fair comparison - only rank drivers who have reached furthestReachedWp
            if (furthestReachedWp) {
                const overallRanked = [...entries]
                    .filter(e => e.waypointData[furthestReachedWp]?.overallTime)
                    .sort((a, b) => a.waypointData[furthestReachedWp].overallTime - b.waypointData[furthestReachedWp].overallTime);

                const overallLeaderTime = overallRanked[0]?.waypointData[furthestReachedWp]?.overallTime || 0;

                overallRanked.forEach((entry, idx) => {
                    entry.classOverallPos = idx + 1;
                    entry.classOverallGap = entry.waypointData[furthestReachedWp].overallTime - overallLeaderTime;
                    entry.overallAtWp = furthestReachedWp;
                });

                // Drivers who haven't reached the furthest waypoint yet get no position
                entries.filter(e => !e.waypointData[furthestReachedWp]?.overallTime).forEach(e => {
                    e.classOverallPos = null;
                    e.classOverallGap = null;
                    e.overallAtWp = null;
                });
            } else {
                entries.forEach(e => {
                    e.classOverallPos = null;
                    e.classOverallGap = null;
                    e.overallAtWp = null;
                });
            }
            
            // Calculate class-relative positions for each WAYPOINT
            allWaypoints.forEach(wp => {
                const wpRanked = [...entries]
                    .filter(e => e.waypointData[wp]?.stageTime)
                    .sort((a, b) => a.waypointData[wp].stageTime - b.waypointData[wp].stageTime);
                
                const wpLeaderTime = wpRanked[0]?.waypointData[wp]?.stageTime || 0;
                
                wpRanked.forEach((entry, idx) => {
                    entry.waypointData[wp].classPos = idx + 1;
                    entry.waypointData[wp].classGap = entry.waypointData[wp].stageTime - wpLeaderTime;
                });
            });
            
            return entries;
        }
        
        function getSortIndicator(column) {
            const isActive = sortColumn === column;
            return `<span class="sort-indicator ${isActive ? 'active' : ''}">▼</span>`;
        }

        function renderTable(entries) {
            const totalInClass = entries.length;
            const hasData = entries.filter(e => e.classStagePos).length;
            const onStage = entries.filter(e => e.hasStarted && !e.classStagePos).length;
            const notStarted = entries.filter(e => !e.hasStarted).length;
            
            const classInfo = CLASS_CONFIG[currentCategory]?.classes[currentClass];
            const className = classInfo?.name || 'All';
            
            document.getElementById('stats').innerHTML = `
                <div class="flex items-center gap-2"><strong>${className}</strong></div>
                <div class="flex items-center gap-2">🏁 <strong>${totalInClass}</strong> Competitors</div>
                <div class="flex items-center gap-2">📍 <strong>${hasData}</strong> At Waypoints</div>
                <div class="flex items-center gap-2">🚗 <strong>${onStage}</strong> On Stage</div>
                <div class="flex items-center gap-2">⏳ <strong>${notStarted}</strong> Waiting</div>
            `;
            
            if (entries.length === 0) {
                document.getElementById('content').innerHTML = `
                    <div class="p-12 text-center">
                        <p class="text-gray-500">No competitors in this class for the selected stage</p>
                    </div>
                `;
                return;
            }
            
            let wpHeaders = allWaypoints.map((wp, idx) =>
                `<th class="wp-cell px-2 py-2 text-center border-l border-gray-600 sortable" onclick="sortBy('wp_${wp}')">
                    <div class="font-semibold">WP${wp.slice(2)} ${getSortIndicator('wp_' + wp)}</div>
                </th>`
            ).join('');
            
            let html = `
                <div class="table-scroll">
                <table class="w-full">
                <thead>
                <tr class="bg-gray-800 text-white text-sm">
                    <th class="sticky-col bg-gray-800 w-72 px-2 py-3 text-left">Driver / Vehicle</th>
                    <th class="w-16 px-2 py-3 text-center border-l border-gray-600 sortable" onclick="sortBy('startPos')">
                        Start ${getSortIndicator('startPos')}
                    </th>
                    ${wpHeaders}
                    <th class="w-28 px-2 py-3 text-center border-l border-gray-600 bg-blue-900 sortable" onclick="sortBy('classStagePos')">
                        <div>Stage ${getSortIndicator('classStagePos')}</div>
                        <div class="text-xs text-blue-300">${stageComparisonWp ? '@WP' + stageComparisonWp.slice(2) : 'in Class'}</div>
                    </th>
                    <th class="w-28 px-2 py-3 text-center border-l border-gray-600 bg-green-900 sortable" onclick="sortBy('classOverallPos')">
                        <div>Rally ${getSortIndicator('classOverallPos')}</div>
                        <div class="text-xs text-green-300">${stageComparisonWp ? '@WP' + stageComparisonWp.slice(2) : 'in Class'}</div>
                    </th>
                </tr>
                </thead>
                <tbody>
            `;
            
            entries.forEach((e, idx) => {
                const stagePos = e.classStagePos;
                const posClass = stagePos === 1 ? 'pos-1' : stagePos === 2 ? 'pos-2' : stagePos === 3 ? 'pos-3' : '';
                const rowBg = e.isW2RC ? 'bg-amber-50' : (idx % 2 === 0 ? 'bg-white' : 'bg-gray-50');
                const stageMedal = stagePos === 1 ? '🥇' : stagePos === 2 ? '🥈' : stagePos === 3 ? '🥉' : '';
                
                let wpCells = allWaypoints.map(wp => {
                    const wpData = e.waypointData[wp];
                    if (wpData && wpData.stageTime) {
                        const posColor = wpData.classPos <= 3 ? 'text-amber-600 font-bold' : 'text-gray-700';
                        return `<td class="wp-cell px-2 py-2 text-center border-l border-gray-200">
                            <div class="${posColor}">P${wpData.classPos || '-'}</div>
                            <div class="text-xs text-gray-600 font-mono">${formatTime(wpData.stageTime)}</div>
                            <div class="text-xs text-red-600">${formatGap(wpData.classGap)}</div>
                        </td>`;
                    }
                    return `<td class="wp-cell px-2 py-2 text-center border-l border-gray-200 text-gray-300">-</td>`;
                }).join('');
                
                const photoHtml = e.driverPhoto 
                    ? `<img src="${e.driverPhoto}" class="driver-photo" onerror="this.style.display='none'" alt="">`
                    : `<div class="driver-photo bg-gray-200 flex items-center justify-center text-gray-400 text-lg">${getFlag(e.nationality)}</div>`;
                
                html += `
                    <tr class="${rowBg} hover:bg-blue-50 transition-colors border-b border-gray-200">
                        <td class="sticky-col ${rowBg} ${posClass} w-72 px-2 py-2">
                            <div class="flex items-center gap-2">
                                ${photoHtml}
                                <div class="min-w-0">
                                    <div class="flex items-center gap-1">
                                        <span class="bg-gray-800 text-white px-1.5 py-0.5 rounded text-xs font-mono">${e.bib}</span>
                                        <span class="text-sm">${getFlag(e.nationality)}</span>
                                        <span class="font-semibold text-sm truncate">${e.driver}</span>
                                    </div>
                                    <div class="text-xs text-gray-500 truncate">${e.brand || ''} ${e.model || ''}</div>
                                </div>
                            </div>
                        </td>
                        <td class="w-16 px-2 py-2 text-center border-l border-gray-200">
                            <div class="text-sm font-semibold">${e.startPos || '-'}</div>
                            <div class="text-xs ${e.hasStarted ? 'text-green-500' : 'text-gray-400'}">${e.hasStarted ? '✓ GO' : '⏳'}</div>
                        </td>
                        ${wpCells}
                        <td class="w-28 px-2 py-2 text-center border-l border-gray-200 bg-blue-50">
                            ${e.classStagePos ? `
                                <div class="font-bold text-blue-700">P${e.classStagePos}</div>
                                <div class="font-mono text-blue-800">${formatTime(stageComparisonWp ? e.waypointData[stageComparisonWp]?.stageTime : e.latestStageTime)}</div>
                                <div class="text-xs text-red-600 font-semibold">${formatGap(e.classStageGap)}</div>
                            ` : '<span class="text-gray-400">—</span>'}
                        </td>
                        <td class="w-28 px-2 py-2 text-center border-l border-gray-200 bg-green-50">
                            ${e.classOverallPos ? `
                                <div class="font-bold text-green-700">P${e.classOverallPos}</div>
                                <div class="font-mono text-green-800 text-sm">${formatTime(stageComparisonWp ? e.waypointData[stageComparisonWp]?.overallTime : null)}</div>
                                <div class="text-xs text-red-600 font-semibold">${formatGap(e.classOverallGap)}</div>
                            ` : '<span class="text-gray-400">—</span>'}
                        </td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
            
            document.getElementById('content').innerHTML = html;
            document.getElementById('content').classList.add('fade-in');
        }

        async function fetchData() {
            const stage = document.getElementById('stage').value;
            
            document.getElementById('loading-indicator').classList.remove('hidden');
            document.getElementById('refresh-icon').innerHTML = '<div class="loader" style="width:16px;height:16px;border-width:2px;"></div>';
            
            try {
                const response = await fetch(`/api/lastScore?year=2026&category=${currentCategory}&stage=${stage}`);
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('content').innerHTML = `
                        <div class="p-12 text-center">
                            <p class="text-red-500 font-semibold">Error: ${data.error}</p>
                            <button onclick="fetchData()" class="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">Retry</button>
                        </div>
                    `;
                    return;
                }
                
                if (!data || data.length === 0) {
                    document.getElementById('content').innerHTML = `
                        <div class="p-12 text-center">
                            <p class="text-gray-500">No data available for ${CLASS_CONFIG[currentCategory]?.name || currentCategory} - Stage ${stage}</p>
                            <p class="text-gray-400 text-sm mt-2">This category may not have live timing or the stage hasn't started yet.</p>
                        </div>
                    `;
                    document.getElementById('stats').innerHTML = '<span class="text-gray-500">No data</span>';
                    return;
                }
                
                processedData = processData(data);
                sortAndRender();
                document.getElementById('lastUpdate').textContent = 'Updated: ' + new Date().toLocaleTimeString();
                
            } catch (err) {
                document.getElementById('content').innerHTML = `
                    <div class="p-12 text-center">
                        <p class="text-red-500 font-semibold">Failed to load data</p>
                        <p class="text-gray-500 text-sm mt-2">${err.message}</p>
                        <button onclick="fetchData()" class="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">Retry</button>
                    </div>
                `;
            } finally {
                document.getElementById('loading-indicator').classList.add('hidden');
                document.getElementById('refresh-icon').textContent = '🔄';
                startCountdown();
            }
        }

        // Initialize
        updateClassFilters();
        setCategory('A');
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/lastScore')
def get_last_score():
    year = request.args.get('year', '2026')
    category = request.args.get('category', 'M')
    stage = request.args.get('stage', '8')
    
    url = f"{API_BASE}/lastScore-{year}-{category}-{stage}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/category')
def get_category():
    year = request.args.get('year', '2026')
    url = f"{API_BASE}/category-{year}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🏆 Dakar Rally 2026 Stage Visualizer")
    print("   by Spes Systems")
    print("=" * 60)
    print(f"Starting server at http://localhost:5001")
    print("-" * 60)
    print("Features:")
    print("  • Class-relative positions based on real class membership")
    print("  • Simplified sorting (always P1 to last)")
    print("  • 15 second auto-refresh with countdown timer")
    print("  • Driver photos")
    print("-" * 60)
    print("Feedback: lukas@spes.systems")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)