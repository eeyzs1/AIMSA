#!/usr/bin/env bash
set -uo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
mkdir -p "${BACKUP_PATH}"

PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-aimsa}"
PG_DB="${POSTGRES_DB:-aimsa}"
PG_PASSWORD="${POSTGRES_PASSWORD:-aimsa_secret}"

MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_USER:-aimsa}"
MONGO_PASSWORD="${MONGO_PASSWORD:-aimsa_secret}"
MONGO_DB="${MONGO_DB:-aimsa_logs}"

echo "=== AIMSA Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Backup directory: ${BACKUP_PATH}"

echo "[1/2] Backing up PostgreSQL..."
PGPASSWORD="${PG_PASSWORD}" pg_dump \
    -h "${PG_HOST}" \
    -p "${PG_PORT}" \
    -U "${PG_USER}" \
    -d "${PG_DB}" \
    --format=custom \
    --file="${BACKUP_PATH}/postgres_${TIMESTAMP}.dump" \
    2>&1 && echo "  ✅ PostgreSQL backup completed" || echo "  ❌ PostgreSQL backup failed"

echo "[2/2] Backing up MongoDB..."
mongodump \
    --host "${MONGO_HOST}" \
    --port "${MONGO_PORT}" \
    --username "${MONGO_USER}" \
    --password "${MONGO_PASSWORD}" \
    --authenticationDatabase admin \
    --db "${MONGO_DB}" \
    --out "${BACKUP_PATH}/mongo_${TIMESTAMP}" \
    2>&1 && echo "  ✅ MongoDB backup completed" || echo "  ❌ MongoDB backup failed"

BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" 2>/dev/null | cut -f1)
echo ""
echo "=== Backup Complete ==="
echo "Location: ${BACKUP_PATH}"
echo "Size: ${BACKUP_SIZE}"
echo ""
echo "To restore PostgreSQL:"
echo "  pg_restore -h ${PG_HOST} -U ${PG_USER} -d ${PG_DB} ${BACKUP_PATH}/postgres_${TIMESTAMP}.dump"
echo ""
echo "To restore MongoDB:"
echo "  mongorestore --host ${MONGO_HOST} --username ${MONGO_USER} --password *** --db ${MONGO_DB} ${BACKUP_PATH}/mongo_${TIMESTAMP}/${MONGO_DB}"
