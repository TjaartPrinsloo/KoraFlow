# Installation Scripts

This folder contains scripts for setting up data when deploying to production.

## Scripts

### create_injection_items.py

Creates injection items and their associated medications based on a reference item.

**Prerequisites:**
- Reference item `AMINO-GOLD-0.8ML` must exist
- Reference item must be linked to a Medication
- A selling Price List must exist (or will be created as "Standard Selling")

**Usage:**

```bash
# Method 1: Using bench execute
bench --site [site-name] execute installation_scripts.create_injection_items.run

# Method 2: Using bench console
bench --site [site-name] console
>>> exec(open('installation_scripts/create_injection_items.py').read())
```

**What it creates:**
- 7 injection items (Eco, Gold, Aminowell, Eco Boost, Ruby, Titanium, Ruby Boost)
- 7 medications linked to the items
- Item prices set in the Standard Selling price list

**Note:** The script will skip items that already exist, so it's safe to run multiple times.

