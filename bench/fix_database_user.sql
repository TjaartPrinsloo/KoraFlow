-- Fix Database User for koraflow-site
-- Run this script with: mysql -u root -p < fix_database_user.sql
-- Or with sudo: sudo mysql < fix_database_user.sql

CREATE USER IF NOT EXISTS '_64e6cfac4c3befcd'@'localhost' IDENTIFIED BY 'NQtKKkmaNvAEsbNd';
CREATE DATABASE IF NOT EXISTS `_64e6cfac4c3befcd`;
GRANT ALL PRIVILEGES ON `_64e6cfac4c3befcd`.* TO '_64e6cfac4c3befcd'@'localhost';
FLUSH PRIVILEGES;

-- Verify the user was created
SELECT User, Host FROM mysql.user WHERE User = '_64e6cfac4c3befcd';

-- Show success message
SELECT 'Database user _64e6cfac4c3befcd created successfully!' as status;

