// Store admin key in session storage after verification
let isAuthenticated = false;

function checkAuth() {
    const storedAuth = sessionStorage.getItem('adminAuthenticated');
    if (storedAuth === 'true') {
        document.getElementById('authScreen').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        isAuthenticated = true;
        loadSites();
    }
}

async function authenticate(adminKey) {
    // Replace this with your actual admin key
    const CORRECT_ADMIN_KEY = 'musicmateadmin';
    
    if (adminKey === CORRECT_ADMIN_KEY) {
        // Store the actual admin key instead of just 'true'
        sessionStorage.setItem('adminAuthenticated', adminKey);
        document.getElementById('authScreen').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
        isAuthenticated = true;
        loadSites();
    } else {
        alert('Invalid admin key. Please try again.');
    }
}

async function generateKey(formData) {
    if (!isAuthenticated) return;
    
    try {
        const response = await fetch('/api/v1/register-site', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': sessionStorage.getItem('adminAuthenticated')
            },
            body: JSON.stringify({
                site_url: formData.get('site_url'),
                site_name: formData.get('site_name'),
                owner_email: formData.get('owner_email')
            })
        });
        
        const data = await response.json();
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
    if (!isAuthenticated) return;
    
    try {
        const response = await fetch('/api/v1/sites', {
            headers: {
                'X-Admin-Key': sessionStorage.getItem('adminAuthenticated')
            }
        });
        const sites = await response.json();
        
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
    if (!isAuthenticated) return;
    
    if (!confirm('Are you sure you want to revoke this key?')) return;
    
    try {
        await fetch('/api/v1/revoke-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': sessionStorage.getItem('adminAuthenticated')
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
    // Check authentication status
    checkAuth();
    
    // Auth form listener
    const authForm = document.getElementById('authForm');
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const adminKey = document.getElementById('adminKeyInput').value;
        await authenticate(adminKey);
    });

    // Generate key form listener
    const generateKeyForm = document.getElementById('generateKeyForm');
    generateKeyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateKey(new FormData(e.target));
    });
});