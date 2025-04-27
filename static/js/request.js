document.addEventListener('DOMContentLoaded', function () {
    const requestForm = document.getElementById('requestForm');

    requestForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = {
            companyName: document.getElementById('companyName').value,
            shortCode: document.getElementById('shortCode').value,
            color: document.getElementById('color').value,
            additionalUsers: document.getElementById('additionalUsers').value
                ? document.getElementById('additionalUsers').value
                    .split(',')
                    .map(id => id.trim())
                    .filter(id => id.length > 0)
                : [],
            companyUid: document.getElementById('companyUid').value
        };

        try {
            const response = await fetch('/api/operators/request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                alert('Your request has been successfully submitted!');
                window.location.href = '/operators';
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
                console.error('Error:', data);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error while submitting the request. Please try again later.');
        }
    });
});