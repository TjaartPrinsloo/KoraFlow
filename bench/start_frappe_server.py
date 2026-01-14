#!/usr/bin/env python3
import sys
import os
import subprocess
import time

# Set up paths
bench_path = "/Users/tjaartprinsloo/Documents/KoraFlow/bench"
sites_path = os.path.join(bench_path, "sites")
apps_path = os.path.join(bench_path, "apps")

# Change to sites directory (where apps.txt is)
os.chdir(sites_path)

# Add apps to Python path
sys.path.insert(0, apps_path)

# Set environment
env = os.environ.copy()
env['PYTHONPATH'] = apps_path + ':' + env.get('PYTHONPATH', '')

# Start the server
print(f"Starting Frappe server from {sites_path}...")
print(f"Apps path: {apps_path}")
print(f"Apps.txt exists: {os.path.exists('apps.txt')}")

proc = subprocess.Popen(
    [sys.executable, '-m', 'frappe.utils.bench_helper', 'frappe', 'serve', '--port', '8000'],
    cwd=sites_path,
    env=env,
    stdout=open('/tmp/frappe_serve.log', 'w'),
    stderr=subprocess.STDOUT
)

print(f"Server started with PID: {proc.pid}")
print("Waiting for server to start...")
time.sleep(15)

# Check if it's running
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000', timeout=2)
    print(f"✓ Server is responding! Status: {response.getcode()}")
except Exception as e:
    print(f"Server may still be starting. Check logs: tail -f /tmp/frappe_serve.log")
    print(f"Error: {e}")

print(f"\nServer process PID: {proc.pid}")
print("To stop: kill", proc.pid)

