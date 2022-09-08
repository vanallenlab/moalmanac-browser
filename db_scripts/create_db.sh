#!/bin/bash

# Create database from TSV import file
# Usage:
# bash create_db.sh <feature definitions file> <assertions folder> <db name> <major version> <minor version> <patch version>
# Example: bash Example: create_db.sh features_file.tsv assertions_folder/*.txt almanac 1 2 3
# Set create/drop locations below

FEATURES_FILE="$1"
DB="$2"
DB_NAME="$3"
V_MAJOR="$4"
V_MINOR="$5"
V_PATCH="$6"
RELEASE="$7"

SCRIPT_DIR="db_scripts"
DROP_SCRIPT="$SCRIPT_DIR/db_drop.sql"
CREATE_SCRIPT="$SCRIPT_DIR/db_create.sql"
INSERT_SCRIPT="$SCRIPT_DIR/db_insert.py"

if [[ "$#" -ne 7 ]]; then
	echo 'Usage:'
	echo 'create_db.sh <feature definitions file> <assertions folder> <db name> <major version> <minor version> <patch version> <content release>'
	echo 'Example: bash create_db.sh features_file.tsv assertions_folder/*.txt almanac 1 2 3'
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
cat "$DROP_SCRIPT" |
    sqlite3 "$DB_NAME" 2>&1 |
    sed -r 's/^Error: near line ([[:digit:]]+): no such table: (.*)/\tTable \2 does not exist, skipping (line \1)./g'
echo "Creating tables..."
cat "$CREATE_SCRIPT" | sqlite3 "$DB_NAME"
echo 'Importing data:'
echo -e "\tFeatures file  : ${FEATURES_FILE}"
echo -e "\tAssertions folder: ${ASSERTIONS_FOLDER}"
echo -e "\tOutput database: ${DB_NAME}"
echo -e "\tVersion        : ${V_MAJOR}.${V_MINOR}.${V_PATCH} ${RELEASE}"
python "$INSERT_SCRIPT" --features_tsv "$FEATURES_FILE" --database "$DB" --db_filename "$DB_NAME" --version_major "$V_MAJOR" --version_minor "$V_MINOR" --version_patch "$V_PATCH" --version_data_release "$RELEASE"

#OUTPUT_FILE=${DB_NAME}.${V_MAJOR}.${V_MINOR}.${V_PATCH}.${RELEASE}.sqlite3
OUTPUT_FILE=${DB_NAME}.sqlite3
mv ${DB_NAME} ${OUTPUT_FILE}
mv ${OUTPUT_FILE} db_versions/

echo "Finished."
