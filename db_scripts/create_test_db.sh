#!/bin/sh

DB_NAME="target.sqlite3"
SCRIPT_DIR="db_scripts"

echo "Dropping tables..."
cat "$SCRIPT_DIR/TARGET_drop.sql" | sqlite3 "$DB_NAME"
echo "Creating tables..."
cat "$SCRIPT_DIR/TARGET_create.sql" | sqlite3 "$DB_NAME"
echo "Inserting test data..."
python "$SCRIPT_DIR/TARGET_test_insert.py"

echo "Finished."
