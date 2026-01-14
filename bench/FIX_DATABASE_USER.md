# Fix Database User for koraflow-site

The database user `_64e6cfac4c3befcd` needs to be created or have its password reset.

## Option 1: Using MySQL Command Line (Recommended)

Run these commands in your terminal:

```bash
mysql -u root -p
```

Then paste these SQL commands:

```sql
CREATE USER IF NOT EXISTS '_64e6cfac4c3befcd'@'localhost' IDENTIFIED BY 'NQtKKkmaNvAEsbNd';
CREATE DATABASE IF NOT EXISTS `_64e6cfac4c3befcd`;
GRANT ALL PRIVILEGES ON `_64e6cfac4c3befcd`.* TO '_64e6cfac4c3befcd'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Option 2: If root password doesn't work, use sudo

```bash
sudo mysql
```

Then run the same SQL commands as above (without the password prompt).

## Option 3: One-liner (if you know root password)

```bash
mysql -u root -p -e "CREATE USER IF NOT EXISTS '_64e6cfac4c3befcd'@'localhost' IDENTIFIED BY 'NQtKKkmaNvAEsbNd'; CREATE DATABASE IF NOT EXISTS \`_64e6cfac4c3befcd\`; GRANT ALL PRIVILEGES ON \`_64e6cfac4c3befcd\`.* TO '_64e6cfac4c3befcd'@'localhost'; FLUSH PRIVILEGES;"
```

## Verify the fix

After running the commands, test the connection:

```bash
mysql -u '_64e6cfac4c3befcd' -p'NQtKKkmaNvAEsbNd' -e "SELECT 1;"
```

If this works, restart the Frappe server:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
kill $(lsof -ti:8000) 2>/dev/null
source env/bin/activate
export PYTHONPATH="/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps:$PYTHONPATH"
cd sites
python3 -m frappe.utils.bench_helper frappe serve --port 8000
```

## Database Configuration

Current settings from `sites/koraflow-site/site_config.json`:
- Database name: `_64e6cfac4c3befcd`
- Database user: `_64e6cfac4c3befcd`
- Database password: `NQtKKkmaNvAEsbNd`
- Database host: `localhost`

