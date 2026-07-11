import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update const viewer = ...
content = content.replace("const viewer = document.getElementById('viewer-image');", "const viewer = document.getElementById('transform-wrapper');\n        const viewerImage = document.getElementById('viewer-image');")

# 2. Add some state variables
state_vars = """
        let allImages = [];
        let images = [];
        let currentIndex = 0;
        
        let viewMode = 'single'; // single, xlarge, large, medium, small
        let pendingDecision = null;
        let selectedReason = null;
"""
content = re.sub(r"let allImages = \[\];[\s\S]*?let selectedReason = null;", state_vars, content)

# 3. Add changeViewMode, renderBrowserGrid, updateBrowserStats, selectThumbnail, openInspector, closeInspector
new_functions = """
        function changeViewMode() {
            viewMode = document.getElementById('view-mode').value;
            if (viewMode === 'single') {
                openInspector();
            } else {
                closeInspector();
                renderBrowserGrid();
            }
        }
        
        function updateBrowserStats() {
            if (!totalStats) return;
            const keep = allImages.filter(i => i.classification === 'KEEP').length;
            const review = allImages.filter(i => i.classification === 'REVIEW').length;
            const reject = allImages.filter(i => i.classification === 'REJECT').length;
            document.getElementById('browser-stats').innerHTML = 
                `${allImages.length} Images | <span style="color:#50cd32">KEEP: ${keep}</span> | <span style="color:#ffd700">REVIEW: ${review}</span> | <span style="color:#dc143c">REJECT: ${reject}</span>`;
        }
        
        function renderBrowserGrid() {
            const grid = document.getElementById('thumbnail-grid');
            grid.innerHTML = '';
            
            let minWidth = '150px';
            if (viewMode === 'xlarge') minWidth = '400px';
            else if (viewMode === 'large') minWidth = '250px';
            else if (viewMode === 'medium') minWidth = '150px';
            else if (viewMode === 'small') minWidth = '100px';
            
            grid.style.gridTemplateColumns = `repeat(auto-fill, minmax(${minWidth}, 1fr))`;
            
            images.forEach((img, idx) => {
                const div = document.createElement('div');
                div.className = 'thumb-item' + (idx === currentIndex ? ' selected' : '');
                div.id = 'thumb-' + idx;
                
                const imgEl = document.createElement('img');
                imgEl.src = `/api/images/${img.filename}`;
                imgEl.loading = 'lazy';
                
                div.appendChild(imgEl);
                
                div.onclick = () => selectThumbnail(idx);
                div.ondblclick = () => { selectThumbnail(idx); document.getElementById('view-mode').value = 'single'; changeViewMode(); };
                
                grid.appendChild(div);
            });
            updateBrowserStats();
            scrollToSelectedThumbnail();
        }
        
        function selectThumbnail(index) {
            if (index < 0 || index >= images.length) return;
            const oldThumb = document.getElementById('thumb-' + currentIndex);
            if (oldThumb) oldThumb.classList.remove('selected');
            
            currentIndex = index;
            
            const newThumb = document.getElementById('thumb-' + currentIndex);
            if (newThumb) newThumb.classList.add('selected');
            scrollToSelectedThumbnail();
        }
        
        function scrollToSelectedThumbnail() {
            if (viewMode === 'single') return;
            const thumb = document.getElementById('thumb-' + currentIndex);
            if (thumb) {
                thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        function openInspector() {
            document.getElementById('browser-container').style.display = 'none';
            document.getElementById('viewer-container').style.display = 'flex';
            loadImage(currentIndex);
        }
        
        function closeInspector() {
            document.getElementById('viewer-container').style.display = 'none';
            document.getElementById('browser-container').style.display = 'flex';
        }
        
        function updateBurstPanel() {
            const panel = document.getElementById('burst-panel');
            const strip = document.getElementById('burst-strip');
            const title = document.getElementById('burst-title');
            strip.innerHTML = '';
            
            const currentImg = images[currentIndex];
            if (!currentImg || !currentImg.duplicate_group_id) {
                panel.style.display = 'none';
                return;
            }
            
            const burstImages = allImages.filter(i => i.duplicate_group_id === currentImg.duplicate_group_id);
            if (burstImages.length <= 1) {
                panel.style.display = 'none';
                return;
            }
            
            title.innerText = `Burst ${currentImg.duplicate_group_id} (${burstImages.length} Images)`;
            panel.style.display = 'flex';
            
            burstImages.forEach(bImg => {
                const div = document.createElement('div');
                div.className = 'burst-thumb' + (bImg.is_best_frame ? ' winner' : '');
                
                // If it's the current image, give it a blue border
                if (bImg.filename === currentImg.filename) {
                    div.style.borderColor = '#007acc';
                }
                
                const imgEl = document.createElement('img');
                imgEl.src = `/api/images/${bImg.filename}`;
                imgEl.loading = 'lazy';
                
                div.appendChild(imgEl);
                
                div.onclick = () => {
                    const targetIdx = images.findIndex(i => i.filename === bImg.filename);
                    if (targetIdx !== -1) {
                        loadImage(targetIdx);
                    }
                };
                
                strip.appendChild(div);
            });
        }
"""
content = content.replace("async function fetchStats() {", new_functions + "\n        async function fetchStats() {")

# 4. Modify loadImage to call updateBurstPanel and set viewerImage.src
content = content.replace("viewer.src = `/api/image/${img.filename}`;", "viewerImage.src = `/api/images/${img.filename}`;\n            updateBurstPanel();")
# also need to handle the old api path typo just in case (the regex replaced image -> images already maybe)

# 5. Modify keyboard logic
keyboard_logic_old = """
            if (images.length === 0) return;
            
            const key = e.key.toUpperCase();
            if (key === 'A') sendFeedback(images[currentIndex].classification, "", "", "Agreement");
            else if (key === 'K') openModal('KEEP');
            else if (key === 'V') openModal('REVIEW');
            else if (key === 'R') openModal('REJECT');
            else if (key === 'S') sendFeedback('SKIPPED', "", "", "Skipped");
            else if (key === 'Z') {
                if (zoomLevel > 1) resetZoom();
                else { zoomLevel = 2; setTransform(); }
            } else if (e.key === 'ArrowRight') {
                if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
            } else if (e.key === 'ArrowLeft') {
                if (currentIndex > 0) loadImage(currentIndex - 1);
            }
        });
"""
keyboard_logic_new = """
            if (images.length === 0) return;
            
            const key = e.key.toUpperCase();
            
            if (viewMode !== 'single') {
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    if (currentIndex < images.length - 1) selectThumbnail(currentIndex + 1);
                    e.preventDefault();
                } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    if (currentIndex > 0) selectThumbnail(currentIndex - 1);
                    e.preventDefault();
                } else if (e.key === 'Enter') {
                    document.getElementById('view-mode').value = 'single';
                    changeViewMode();
                }
                return;
            }
            
            if (e.key === 'Escape' && viewMode === 'single') {
                document.getElementById('view-mode').value = 'medium'; // default back to medium or previous
                changeViewMode();
                return;
            }
            
            if (key === 'A') sendFeedback(images[currentIndex].classification, "", "", "Agreement");
            else if (key === 'K') openModal('KEEP');
            else if (key === 'V') openModal('REVIEW');
            else if (key === 'R') openModal('REJECT');
            else if (key === 'S') sendFeedback('SKIPPED', "", "", "Skipped");
            else if (key === 'Z') {
                if (zoomLevel > 1) resetZoom();
                else { zoomLevel = 2; setTransform(); }
            } else if (e.key === 'ArrowRight') {
                if (currentIndex < images.length - 1) loadImage(currentIndex + 1);
            } else if (e.key === 'ArrowLeft') {
                if (currentIndex > 0) loadImage(currentIndex - 1);
            }
        });
"""
content = content.replace(keyboard_logic_old.strip(), keyboard_logic_new.strip())

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML modified successfully.")
