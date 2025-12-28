#!/bin/bash
# MariaDB wrapper that uses Docker
docker exec -i koraflow-mariadb mariadb "$@"

