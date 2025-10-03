function openModal() {
    const modal = document.getElementById("modal");
    modal.style.display = "block";
    modal.offsetHeight;
    requestAnimationFrame(() => {
        document.body.classList.add('blur');
        modal.classList.add('show');
    });
}

function closeModal() {
    const modal = document.getElementById("modal");
    document.body.classList.remove('blur');
    modal.classList.remove('show');
    
    modal.addEventListener('transitionend', function hideModal(e) {
        if (e.propertyName === 'opacity') {
            modal.style.display = "none";
            modal.removeEventListener('transitionend', hideModal);
        }
    });
}

async function getOperatorColor(operatorUid) {
    try {
        const response = await fetch('/operators.json');
        const operators = await response.json();
        const operator = operators.find(op => op.uid === operatorUid);
        return operator?.color || '#808080';
    } catch (error) {
        console.error('Error fetching operator color:', error);
        return '#808080';
    }
}

let linesData = [];

function fetchLines() {
    fetch('/lines.json')
        .then(response => response.json())
        .then(linesArray => {
            linesData = linesArray;
            const lines = {};
            linesArray.forEach(line => {
                lines[line.name] = line.color;
            });

            document.querySelectorAll('.line-item').forEach(element => {
                const lineName = element.dataset.line;
                if (lines[lineName]) {
                    element.style.backgroundColor = lines[lineName];
                }
            });

            const modal = document.getElementById("modal");
            const modalContent = document.getElementById("modal-inner");

            // Remove any existing event listeners to prevent duplicates
            document.querySelectorAll(".line").forEach(lineElement => {
                // Clone the element to remove all event listeners
                const newElement = lineElement.cloneNode(true);
                lineElement.parentNode.replaceChild(newElement, lineElement);
            });

            // Add fresh event listeners
            document.querySelectorAll(".line").forEach(lineElement => {
                lineElement.addEventListener("click", async () => {
                    const clickedLineName = lineElement.dataset.line;
                    const lineData = linesData.find(line => line.name === clickedLineName);

                    if (lineData) {
                        const statusEmoji = (() => {
                            switch(lineData.status) {
                                case 'Running': return '✅';
                                case 'Possible delays': return '⚠️';
                                case 'No scheduled service': return '🌙';
                                case 'Partially suspended': return '〽️';
                                case 'Suspended': return '🚫';
                                default: return '';
                            }
                        })();

                        const operatorColor = await getOperatorColor(lineData.operator_uid);

                        const operatorName = await fetch('/operators.json')
                            .then(response => response.json())
                            .then(operators => {
                                const operator = operators.find(op => op.uid === lineData.operator_uid);
                                return operator?.name || 'Unknown Operator';
                            })
                            .catch(error => {
                                console.error('Error fetching operator name:', error);
                                return 'Unknown Operator';
                            });

                        const fgColor = getContrastColor(lineData.color);
                        const operatorFgColor = getContrastColor(operatorColor);

                        modalContent.innerHTML = `
                            <div style="display: flex; align-items: center">
                                <h1 class="line-modal" style="background-color: ${lineData.color}; color: ${fgColor}">${lineData.name}</h1>
                                <span style="margin-left: 16px; background-color: ${operatorColor}; color: ${operatorFgColor}" class="line-modal" onclick="window.location.href = '/operators/${lineData.operator_uid || ''}'">${operatorName || ''}</span>
                            </div>
                            <h3>${statusEmoji} ${lineData.status || 'No description available'}</h3>
                            <p>${(lineData.notice && lineData.notice.trim() !== '') ? lineData.notice.trim() : 'No notice available'}</p>
                            <hr>
                        `;

                        if (!lineData.stations || lineData.stations.length === 0) {
                            modalContent.innerHTML += `<p>Station list not available</p>`;
                        } else {
                            modalContent.innerHTML += `<h2>Stations</h2>`;
                            const ul = document.createElement("ul");
                            if (lineData.stations.length === 1 && lineData.stations[0].startsWith('<content:html>')) {
                                modalContent.innerHTML += lineData.stations[0].replace('<content:html>', '').replace("<script>", "").replace("</script>", "");
                            } else {
                                lineData.stations.forEach(station => {
                                    const li = document.createElement("li");
                                    li.innerHTML = station;
                                    ul.appendChild(li);
                                });
                                modalContent.appendChild(ul);
                            }
                        }

                        // Add train composition(s)
                        const compositions = lineData.compositions || (lineData.composition ? [lineData.composition] : []);
                        
                        if (compositions.length > 0 && compositions.some(c => {
                            if (typeof c === 'string') return c.trim() !== '';
                            if (typeof c === 'object') return c.parts && c.parts.trim() !== '';
                            return false;
                        })) {
                            const compositionDiv = document.createElement("div");
                            compositionDiv.style.marginTop = "20px";
                            compositionDiv.innerHTML = `<h2>Train Composition${compositions.length > 1 ? 's' : ''}</h2>`;
                            
                            compositions.forEach((composition, index) => {
                                let parts = '';
                                let variantName = '';
                                
                                // Handle both old format (string) and new format (object)
                                if (typeof composition === 'string') {
                                    parts = composition;
                                } else if (composition && typeof composition === 'object') {
                                    parts = composition.parts || '';
                                    variantName = composition.name || '';
                                }
                                
                                if (parts && parts.trim() !== '') {
                                    if (compositions.length > 1 || variantName) {
                                        const variantLabel = document.createElement("h3");
                                        variantLabel.textContent = variantName || `Variant ${index + 1}`;
                                        variantLabel.style.marginTop = index > 0 ? "15px" : "0";
                                        variantLabel.style.marginBottom = "8px";
                                        compositionDiv.appendChild(variantLabel);
                                    }
                                    
                                    const compositionDisplay = document.createElement("div");
                                    compositionDisplay.className = "composition-display";
                                    
                                    parts.split(',').forEach(part => {
                                        const partDiv = document.createElement("div");
                                        partDiv.className = "composition-part-display";
                                        partDiv.style.backgroundImage = `url('/static/assets/icons/${part}.png')`;
                                        partDiv.title = part.toUpperCase();
                                        compositionDisplay.appendChild(partDiv);
                                    });
                                    
                                    compositionDiv.appendChild(compositionDisplay);
                                }
                            });
                            
                            modalContent.appendChild(compositionDiv);
                        }

                        openModal();
                    }
                });
            });
        })
        .catch(error => {
            console.error('Error fetching lines:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const tabId = tab.dataset.tab;
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Setup modal close handlers once
    const modal = document.getElementById("modal");
    const closeBtn = document.getElementById("close");
    
    if (closeBtn) {
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            closeModal();
        };
    }
    
    window.onclick = (event) => {
        if (event.target === modal) {
            closeModal();
        }
    };
    
    window.addEventListener('keydown', (event) => {
        if (event.key === "Escape") {
            closeModal();
        }
    });
});

function filterLinesByType(type) {
    document.querySelectorAll('.line-item').forEach(line => {
        const lineName = line.dataset.line;
        const lineData = linesData.find(l => l.name === lineName);
        
        if (lineData && lineData.type === type) {
            line.style.display = 'block';
        } else {
            line.style.display = 'none';
        }
    });
}


function setContrastColor(elementId, color) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    try {
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0,2), 16);
        const g = parseInt(hex.substr(2,2), 16);
        const b = parseInt(hex.substr(4,2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        
        element.style.color = brightness > 128 ? '#000000' : '#ffffff';
    } catch (error) {
        console.error(`Error setting colors for ${elementId}:`, error);
    }
}


function getContrastColor(color) {
    try {
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0,2), 16);
        const g = parseInt(hex.substr(2,2), 16);
        const b = parseInt(hex.substr(4,2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        
        return brightness > 128 ? '#000000' : '#ffffff';
    } catch (error) {
        console.error('Error calculating contrast color:', error);
        return '#000000'; 
    }
}