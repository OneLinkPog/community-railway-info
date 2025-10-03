document.addEventListener('DOMContentLoaded', function() {
    const operatorForm = document.getElementById('operatorForm');
    if (operatorForm) {
        operatorForm.addEventListener('submit', handleOperatorSubmit);
    }

    // Drag and Drop for Train Composition - Multiple variants support
    const compositionPartContainer = document.getElementById('composition-parts');
    const compositionsContainer = document.getElementById('compositions-container');
    const lineCompositionInput = document.getElementById('lineComposition');

    let draggedItem = null;
    let isFromSource = false;
    let compositionVariants = [];

    window.addCompositionVariant = function() {
        const variantIndex = compositionVariants.length;
        const variantDiv = document.createElement('div');
        variantDiv.className = 'composition-variant';
        variantDiv.style.marginBottom = '15px';
        variantDiv.dataset.index = variantIndex;
        
        variantDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                <label><b>Variant ${variantIndex + 1}</b></label>
                <button type="button" class="btn-danger" onclick="removeCompositionVariant(${variantIndex})" style="padding: 4px 8px; font-size: 12px;">
                    <span class="material-symbols-outlined" style="font-size: 16px;">delete</span>
                </button>
            </div>
            <div class="composition-dropzone form-make-this-shit-white" data-variant="${variantIndex}"></div>
        `;
        
        compositionsContainer.appendChild(variantDiv);
        compositionVariants.push([]);
        
        const dropzone = variantDiv.querySelector('.composition-dropzone');
        setupDropzone(dropzone, variantIndex);
        updateCompositionInput();
    };

    window.removeCompositionVariant = function(index) {
        const variantDiv = document.querySelector(`.composition-variant[data-index="${index}"]`);
        if (variantDiv) {
            variantDiv.remove();
            compositionVariants[index] = null; // Mark as deleted
            updateCompositionInput();
        }
    };

    function setupDraggable(item) {
        item.addEventListener('dragstart', (e) => {
            draggedItem = item;
            const dropzone = item.parentElement;
            isFromSource = !dropzone.classList.contains('composition-dropzone');
            e.dataTransfer.setData('text/plain', item.dataset.part);
            setTimeout(() => {
                item.classList.add('dragging');
            }, 0);
        });

        item.addEventListener('dragend', () => {
            if (draggedItem) {
                draggedItem.classList.remove('dragging');
            }
            draggedItem = null;
        });
    }

    function setupDropzone(dropzone, variantIndex) {
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(dropzone, e.clientX);
            const draggable = document.querySelector('.dragging');
            // Only move elements that are already in this dropzone (reordering)
            if (draggable && draggable.parentElement === dropzone) {
                if (afterElement == null) {
                    dropzone.appendChild(draggable);
                } else {
                    dropzone.insertBefore(draggable, afterElement);
                }
            }
        });

        dropzone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dropzone.style.border = '2px solid #007bff';
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.style.border = '2px dashed #ccc';
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            if (!draggedItem) return;

            if (isFromSource) {
                const newPart = draggedItem.cloneNode(true);
                newPart.classList.remove('dragging');
                const partName = newPart.getAttribute('data-part');
                newPart.style.backgroundImage = `url('/static/assets/icons/${partName}.png')`;
                newPart.addEventListener('click', () => {
                    dropzone.removeChild(newPart);
                    updateCompositionInput();
                });
                setupDraggable(newPart);
                
                const afterElement = getDragAfterElement(dropzone, e.clientX);
                if (afterElement == null) {
                    dropzone.appendChild(newPart);
                } else {
                    dropzone.insertBefore(newPart, afterElement);
                }
            }
            
            if (draggedItem) {
                draggedItem.classList.remove('dragging');
            }
            updateCompositionInput();
            dropzone.style.border = '2px dashed #ccc';
        });
    }

    compositionPartContainer.querySelectorAll('.composition-part').forEach(setupDraggable);

    function getDragAfterElement(container, x) {
        const draggableElements = [...container.querySelectorAll('.composition-part:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = x - box.left - box.width / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    function updateCompositionInput() {
        if (!compositionsContainer || !lineCompositionInput) return;
        
        const allCompositions = [];
        document.querySelectorAll('.composition-dropzone').forEach(dropzone => {
            const parts = Array.from(dropzone.children).map(p => p.getAttribute('data-part'));
            if (parts.length > 0) {
                allCompositions.push(parts.join(','));
            }
        });
        
        lineCompositionInput.value = JSON.stringify(allCompositions);
        console.log("Compositions updated:", lineCompositionInput.value);
    }

    window.loadCompositions = function(compositions) {
        if (!compositionsContainer) return;
        
        // Clear existing variants
        compositionsContainer.innerHTML = '';
        compositionVariants = [];
        
        // Handle different data formats
        let compositionsArray = [];
        
        if (Array.isArray(compositions)) {
            compositionsArray = compositions;
        } else if (typeof compositions === 'string' && compositions.trim() !== '') {
            // Legacy: single composition string or JSON array
            try {
                const parsed = JSON.parse(compositions);
                compositionsArray = Array.isArray(parsed) ? parsed : [compositions];
            } catch {
                compositionsArray = [compositions];
            }
        }
        
        // Load each composition variant
        if (compositionsArray.length > 0) {
            compositionsArray.forEach((composition, index) => {
                window.addCompositionVariant();
                const dropzone = document.querySelector(`.composition-dropzone[data-variant="${index}"]`);
                if (dropzone && composition) {
                    const parts = composition.split(',');
                    parts.forEach(partId => {
                        if (partId) {
                            const originalPart = document.querySelector(`#composition-parts .composition-part[data-part="${partId}"]`);
                            if (originalPart) {
                                const newPart = originalPart.cloneNode(true);
                                newPart.style.backgroundImage = `url('/static/assets/icons/${partId}.png')`;
                                newPart.addEventListener('click', () => {
                                    dropzone.removeChild(newPart);
                                    updateCompositionInput();
                                });
                                setupDraggable(newPart);
                                dropzone.appendChild(newPart);
                            }
                        }
                    });
                }
            });
        } else {
            // Add one empty variant if none exist
            window.addCompositionVariant();
        }
        
        updateCompositionInput();
    };
});

async function handleOperatorSubmit(event) {
    event.preventDefault();
    console.log('handleOperatorSubmit called');

    const formData = new FormData(event.target);
    const operatorId = window.operatorUid;

    const data = {
        name: formData.get('name'),
        color: formData.get('color'),
        users: formData.get('users').split('\n').filter(s => s.trim()),
        short: formData.get('short'),
    };

    try {
        const method = operatorId ? 'PUT' : 'POST';
        const url = operatorId ? `/api/operators/${operatorId}` : '/api/operators';

        console.log('Sending request:', { method, url, data });

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert('[Server] Error while saving: ' + (error.error || 'Unknown Error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error while saving: ' + error);
    }
}

let currentLine = null;

function showAddLineModal() {
    const modal = document.getElementById('lineModal');
    document.getElementById('lineForm').reset();
    document.getElementById('modalTitle').textContent = 'Add New Line';
    document.getElementById('lineId').value = '';
    if (window.noticeEditor) {
        window.noticeEditor.setValue("");
    }
    window.loadCompositions([]); // Load with empty array
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
        if (window.noticeEditor) {
            window.noticeEditor.refresh();
        }
    }, 10);
}

async function editLine(lineName) {
    const line = window.lines.find(l => l.name === lineName);
    if (!line) {
        console.error('Line not found:', lineName);
        return;
    }

    console.log('Editing Line:', line);
    console.log('Notice:', line.notice); 

    document.getElementById('modalTitle').textContent = 'Edit line';
    document.getElementById('lineName').value = line.name;
    document.getElementById('lineColor').value = line.color || '#000000';
    document.getElementById('lineStatus').value = line.status || 'Running';
    document.getElementById('lineType').value = line.type || 'public';

    if (window.noticeEditor) {
        window.noticeEditor.setValue(line.notice || "");
    }
    
    // Load compositions - supports both old 'composition' and new 'compositions'
    window.loadCompositions(line.compositions || line.composition || []);

    document.getElementById('lineId').value = line.name;
    var stationsField = document.getElementById('lineStations');
    if (stationsField) {
        stationsField.value = (line.stations || []).join('\n');
    }

    const modal = document.getElementById('lineModal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
        if (window.noticeEditor) {
            window.noticeEditor.refresh();
        }
    }, 20);
}

async function editOperator(operatorName) {
// ... existing code ...
    const operator = window.operatorName;
    if (!operator) {
        console.error('Operator not found:', operatorName);
        return;
    }

    console.log('Editing Operator:', operator);

    document.getElementById('modalTitle').textContent = 'Edit operator';
    document.getElementById('operatorName').value = window.operatorName;


    const response = await fetch('/operators.json');
    const operators = await response.json();
    const operatorData = operators.find(op => op.uid === window.operatorUid);

    if (operatorData) {
        document.getElementById('operatorColor').value = operatorData.color || '#000000';
        document.getElementById('operatorUsers').value = (operatorData.users || []).join('\n');
        document.getElementById('operatorShort').value = operatorData.short || '';
        document.getElementById('operatorUid').value = operatorData.uid;
    } else {
        console.error('Operator data not found for UID:', window.operatorUid);
    }

    const modal = document.getElementById('operatorModal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

async function deleteLine(lineName) {
// ... existing code ...
    if (!confirm(`Are you sure you want to delete line ${lineName}?`)) return;

    try {
        const response = await fetch('/api/lines/' + lineName, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert('Error deleting line');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting line');
    }
}

async function handleLineSubmit(event, uid) {
    event.preventDefault();
    if (window.noticeEditor) {
        const noticeValue = window.noticeEditor.getValue();
        const noticeTextarea = document.querySelector('textarea[name="notice"]');
        if (noticeTextarea) {
            noticeTextarea.value = noticeValue;
        }
    }
    const formData = new FormData(event.target);
    const lineId = document.getElementById('lineId').value;

    // Parse compositions from JSON string
    let compositions = [];
    try {
        const compositionsValue = formData.get('compositions');
        if (compositionsValue) {
            compositions = JSON.parse(compositionsValue);
        }
    } catch (e) {
        console.error('Error parsing compositions:', e);
    }

    const data = {
        name: formData.get('name'),
        color: formData.get('color'),
        status: formData.get('status'),
        type: formData.get('type'),       
        notice: formData.get('notice'),
        stations: formData.get('stations').split('\n').filter(s => s.trim()),
        compositions: compositions,
        operator: window.operatorName,
        operator_uid: window.operatorUid    
    };

    try {
        const method = lineId ? 'PUT' : 'POST';
        const url = lineId ? `/api/lines/${lineId}` : '/api/lines';

        console.log('Sending request:', { method, url, data });

        const response = await fetch(url, {
// ... existing code ...
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert('[Server] Error while saving: ' + (error.error || 'Unknown Error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error while saving: ' + error);
    }
}


function closeLineModal() {
// ... existing code ...
    const modal = document.getElementById('lineModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

document.querySelector('.close').addEventListener('click', closeLineModal);

window.addEventListener('click', (event) => {
    const modal = document.getElementById('lineModal');
    if (event.target === modal) {
        closeLineModal();
    }
});

window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeLineModal();
    }
});

function closeOperatorModal() {
// ... existing code ...
    const modal = document.getElementById('operatorModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

document.querySelector('#closeOperator').addEventListener('click', closeOperatorModal);
window.addEventListener('click', (event) => {
    const modal = document.getElementById('operatorModal');
    if (event.target === modal) {
        closeOperatorModal();
    }
});

window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeOperatorModal();
    }
});