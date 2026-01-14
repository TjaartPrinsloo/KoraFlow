// Utility script to retrieve debug logs from localStorage
// Run this in browser console after reproducing the issue: getDebugLogs()

function getDebugLogs() {
	try {
		var logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
		console.log('=== DEBUG LOGS ===');
		console.log(JSON.stringify(logs, null, 2));
		console.log('Total logs:', logs.length);
		return logs;
	} catch(e) {
		console.error('Error reading logs:', e);
		return [];
	}
}

// Make it available globally
window.getDebugLogs = getDebugLogs;

