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
    document.getElementById('lineNotice').value = line.notice || '';
    document.getElementById('lineStations').value = (line.stations || []).join('\n');
    document.getElementById('lineId').value = line.name;

    const modal = document.getElementById('lineModal');
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
            alert('[Server] Error while saving: ' + (error.message || 'Unknown Error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error while saving: ' + error.message);
    }
}

function closeModal() {
    const modal = document.getElementById('lineModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

document.querySelector('.close').addEventListener('click', closeModal);

window.addEventListener('click', (event) => {
    const modal = document.getElementById('lineModal');
    if (event.target === modal) {
        closeModal();
    }
});

window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});