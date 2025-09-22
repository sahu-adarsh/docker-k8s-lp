
const checkHealth = () => {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            document.getElementById('status').innerHTML = 
                `✅ Health Check: ${data.status} - Uptime: ${Math.floor(data.uptime)}s`;
        })
        .catch(error => {
            document.getElementById('status').innerHTML = 
                `❌ Health Check Failed: ${error.message}`;
        });
}
        
const showInfo = () => {
    const infoDiv = document.getElementById('info-display');
    infoDiv.style.display = infoDiv.style.display === 'none' ? 'block' : 'none';
    
    if (infoDiv.style.display === 'block') {
        document.getElementById('hostname').textContent = window.location.hostname;
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        document.getElementById('health-status').textContent = 'Active';
    }
}

setInterval(checkHealth, 30000);

setTimeout(checkHealth, 1000);
