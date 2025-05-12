document.addEventListener('DOMContentLoaded', function() {
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

    const operatorForm = document.getElementById('operatorForm');
    if (operatorForm) {
        operatorForm.addEventListener('submit', handleOperatorSubmit);
    }
});

let currentLine = null;

function showAddLineModal() {
    const modal = document.getElementById('lineModal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

async function editLine(lineName) {
    const line = window.lines.find(l => l.name === lineName);
    if (!line) {
        console.error('Line not found:', lineName);
        return;
    }

    console.log('Editing Line:', line);

    document.getElementById('modalTitle').textContent = 'Edit line';
    document.getElementById('lineName').value = line.name;
    document.getElementById('lineColor').value = line.color || '#000000';
    document.getElementById('lineStatus').value = line.status || 'Running';
    document.getElementById('lineType').value = line.type || 'public';
    document.getElementById('lineNotice').value = line.notice || '';
    document.getElementById('lineStations').value = (line.stations || []).join('\n');
    document.getElementById('lineId').value = line.name;

    const modal = document.getElementById('lineModal');
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

async function editOperator(operatorName) {
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
    const formData = new FormData(event.target);
    const lineId = document.getElementById('lineId').value;

    const data = {
        name: formData.get('name'),
        color: formData.get('color'),
        status: formData.get('status'),
        type: formData.get('type'),       
        notice: formData.get('notice'),
        stations: formData.get('stations').split('\n').filter(s => s.trim()),
        operator: window.operatorName,
        operator_uid: window.operatorUid    
    };

    try {
        const method = lineId ? 'PUT' : 'POST';
        const url = lineId ? `/api/lines/${lineId}` : '/api/lines';

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


function closeLineModal() {
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
