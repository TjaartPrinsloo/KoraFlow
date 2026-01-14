#!/bin/bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
source env/bin/activate
export PYTHONPATH="/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps:$PYTHONPATH"
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench/sites
python3 -m frappe.utils.bench_helper frappe serve --port 8000

