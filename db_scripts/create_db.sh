#!/bin/bash

# Create database from TSV import file
# Usage:
# bash create_db.sh <input filename> <database name> <major version> <minor version> <patch version>
# Example: bash create_db.sh import_file.tsv db_name 1 2 3
# Set create/drop locations below

IMPORT_FILE="$1"
DB_NAME="$2"
V_MAJOR="$3"
V_MINOR="$4"
V_PATCH="$5"

SCRIPT_DIR="db_scripts"
DROP_SCRIPT="$SCRIPT_DIR/db_drop.sql"
CREATE_SCRIPT="$SCRIPT_DIR/db_create.sql"
INSERT_SCRIPT="$SCRIPT_DIR/db_insert.py"

if [[ "$#" -ne 5 ]]; then
	echo 'Usage:'
	echo 'create_db.sh <input filename> <db name> <major version> <minor version> <patch version>'
	echo 'Example: create_db.sh import_file.tsv new_db.sqlite3 1 2 3'
	exit 1
fi

echo "Creating $DB_NAME from import file ${IMPORT_FILE}."

if [[ -e "$DB_NAME" ]]; then
	echo "Warning: $DB_NAME already exists! This script will overwrite $DB_NAME!"
	read -p "Really overwrite $DB_NAME? [y/N] " -n 1 -r
	echo
	if [[ -z "$REPLY" ]] || [[ "$REPLY" =~ [^Yy]$ ]]; then
		echo "Canceled. No changes made."
		exit 1
	fi
fi

echo "Dropping tables..."
cat "$DROP_SCRIPT" | sqlite3 "$DB_NAME"
echo "Creating tables..."
cat "$CREATE_SCRIPT" | sqlite3 "$DB_NAME"
echo 'Importing data:'
echo -e "\tImport file    : ${IMPORT_FILE}"
echo -e "\tOutput database: ${DB_NAME}"
echo -e "\tVersion        : ${V_MAJOR}.${V_MINOR}.${V_PATCH}"
python "$INSERT_SCRIPT" "$IMPORT_FILE" "$DB_NAME" "$V_MAJOR" "$V_MINOR" "$V_PATCH"

OUTPUT_FILE=${DB_NAME}.${V_MAJOR}.${V_MINOR}.${V_PATCH}.sqlite3
mv ${DB_NAME} ${OUTPUT_FILE}
cp ${OUTPUT_FILE} db_versions/

echo "Finished."
