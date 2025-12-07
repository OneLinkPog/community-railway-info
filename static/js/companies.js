async function handleRequest(timestamp, action) {
    try {
        const response = await fetch('/api/admin/companies/handle-request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: timestamp,
                action: action
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Request successfully ${action === 'accept' ? 'accepted' : 'rejected'}`);
            window.location.reload();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error processing request');
    }
}