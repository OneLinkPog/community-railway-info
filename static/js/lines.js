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

                        modalContent.innerHTML = `
                            <div style="display: flex; align-items: center">
                                <h1 class="line-modal" style="background-color: ${lineData.color}">${lineData.name}</h1>
                                <span style="margin-left: 16px; background-color: ${operatorColor}" class="line-modal" onclick="window.location.href = '/operators/${lineData.operator_uid || ''}'">${lineData.operator || ''}</span>
                            </div>
                            <h3>${statusEmoji} ${lineData.status || 'No description available'}</h3>
                            <p>${lineData.notice || 'No notice available'}</p>
                            <hr>
                        `;

                        if (!lineData.stations || lineData.stations.length === 0) {
                            modalContent.innerHTML += `<p>Station list not available</p>`;
                        } else {
                            modalContent.innerHTML += `<h2>Stations</h2>`;
                            const ul = document.createElement("ul");
                            lineData.stations.forEach(station => {
                                const li = document.createElement("li");
                                if (station.includes('<del>')) {
                                    li.innerHTML = station;
                                } else {
                                    li.textContent = station;
                                }
                                ul.appendChild(li);
                            });
                            modalContent.appendChild(ul);
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