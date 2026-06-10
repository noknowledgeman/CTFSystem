#!/bin/bash

EXPECTED="EH2025{33d4fc1c0d28b80a9a3b93f5c2523103fc06520374a231ca55bcf825aa4579f9}"

# Get the file
wget -q -O /tmp/db.sqlite http://localhost:8000/static/db.sqlite
FLAG=$(sqlite3 -noheader -list /tmp/db.sqlite "SELECT secret_flag FROM secrets;")

[ "$EXPECTED" = "$FLAG" ]