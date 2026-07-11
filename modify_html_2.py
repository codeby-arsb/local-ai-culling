with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update sendFeedback to support viewMode
old_sendFeedback_check = """
            if (images.length > 0) {
                loadImage(currentIndex);
            } else {
                fetchImages(); // Refresh if empty
            }
        }
"""
new_sendFeedback_check = """
            if (images.length > 0) {
                if (viewMode === 'single') loadImage(currentIndex);
                else renderBrowserGrid();
            } else {
                fetchImages(); // Refresh if empty
            }
        }
"""
content = content.replace(old_sendFeedback_check.strip(), new_sendFeedback_check.strip())

# Update applyFilters
old_applyFilters = """
            currentIndex = 0;
            if (images.length > 0) {
                viewer.style.display = 'block';
                loadImage(0);
            } else {
                document.getElementById('filename').innerText = "No photos match filter.";
                viewer.style.display = 'none';
                svgLayer.style.display = 'none';
                document.getElementById('ai-class').innerText = "---";
                document.getElementById('ai-confidence').style.display = 'none';
            }
        }
"""
new_applyFilters = """
            currentIndex = 0;
            if (images.length > 0) {
                viewer.style.display = 'flex';
                if (viewMode === 'single') loadImage(0);
                else renderBrowserGrid();
            } else {
                document.getElementById('filename').innerText = "No photos match filter.";
                viewer.style.display = 'none';
                svgLayer.style.display = 'none';
                document.getElementById('ai-class').innerText = "---";
                document.getElementById('ai-confidence').style.display = 'none';
                if (viewMode !== 'single') renderBrowserGrid();
            }
        }
"""
content = content.replace(old_applyFilters.strip(), new_applyFilters.strip())

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixes applied.")
