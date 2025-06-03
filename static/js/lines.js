function openModal() {
    modal.style.display = "block";
    modal.offsetHeight;
    requestAnimationFrame(() => {
        document.body.classList.add('blur');
        modal.classList.add('show');
    });
}

function closeModal() {
    document.body.classList.remove('blur');
    modal.classList.remove('show');
    
    modal.addEventListener('transitionend', function hideModal(e) {
        if (e.propertyName === 'opacity') {
            modal.style.display = "none";
            modal.removeEventListener('transitionend', hideModal);
        }
    });
}

function fetchLines() {
    let linesData = [];
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

                        modalContent.innerHTML = `
                            <div style="display: flex; align-items: center">
                                <h1 class="line-modal" style="background-color: ${lineData.color}">${lineData.name}</h1>
                                <span style="margin-left: 16px; background-color: ${operatorColor}" class="line-modal" onclick="window.location.href = '/operators/${lineData.operator_uid || ''}'">${operatorName || ''}</span>
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
                                    /* if (station.includes('<del>')) {
                                        li.innerHTML = station;
                                    } else {
                                        li.textContent = station;
                                    } */
                                    ul.appendChild(li);
                                });
                                modalContent.appendChild(ul);
                            }
                        }

                        openModal();
                    }
                });
            });

            document.getElementById("close").onclick = (e) => {
                e.stopPropagation();
                closeModal();
            };
            
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

    filterLinesByType('public');
});


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