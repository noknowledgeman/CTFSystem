#!/bin/bash

set +H
PGPASSWORD='w#Q8WxjX^pUX*UFbTxT!7afkGhLZ^K!W' psql -h 192.168.122.101 -p 5432 -U intranet_bydhwzfp -d intranet_db -tAc "SELECT config_value FROM system_config WHERE config_key = 'secret_flag';"
set -H 