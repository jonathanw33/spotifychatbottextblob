// Constants
const ADMIN_KEY = 'somethingsomething';

// Functions
async function generateKey(formData) {
    try {
        const response = await fetch('/api/v1/register-site', {  // Updated path
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': ADMIN_KEY
            },
            body: JSON.stringify({
                site_url: formData.get('site_url'),
                site_name: formData.get('site_name'),
                owner_email: formData.get('owner_email')
            })
        });
        
        const data = await response.json();
        console.log('Response:', data);  // Debug log
        if (data.api_key) {
            alert(`API Key generated: ${data.api_key}`);
            loadSites();
        } else {
            alert('Error generating API key');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error generating API key');
    }
}

async function loadSites() {
    try {
        const response = await fetch('/api/v1/sites', {  // Updated path
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });
        const sites = await response.json();
        console.log('Sites:', sites);  // Debug log
        
        if (!Array.isArray(sites)) {
            console.error('Sites is not an array:', sites);
            return;
        }

        const tbody = document.querySelector('#sitesTable tbody');
        tbody.innerHTML = sites.map(site => `
            <tr>
                <td>${site.site_name}</td>
                <td>${site.site_url}</td>
                <td>${site.api_key}</td>
                <td>${new Date(site.created_at).toLocaleString()}</td>
                <td>
                    <button onclick="revokeKey('${site.api_key}')">Revoke</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading sites:', error);
    }
}

async function revokeKey(apiKey) {
    if (!confirm('Are you sure you want to revoke this key?')) return;
    
    try {
        await fetch('/api/v1/revoke-key', {  // Updated path
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': ADMIN_KEY
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        loadSites();
    } catch (error) {
        console.error('Error revoking key:', error);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generateKeyForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateKey(new FormData(e.target));
    });

    // Load sites on page load
    loadSites();
});