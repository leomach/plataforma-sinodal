#!/bin/bash

# Certifique-se de que o script seja executado na raiz do projeto
if [ ! -f "manage.py" ]; then
    echo "Erro: Este script deve ser executado da raiz do projeto (onde o manage.py está)."
    exit 1
fi

# Definir a data
DATE=$(date +%d%m%Y)
CURRENT_YEAR=$(date +%Y)
BACKUP_FILE="backup_${DATE}.sql"
BACKUP_DIR="/Users/leandromachado/Documents/backups_sinodal/$CURRENT_YEAR"

RAILWAY_URL="postgresql://postgres:gEiJjgYgVRFgoODJdZGfrZstUOqyxFTT@kodama.proxy.rlwy.net:49615/railway"
LOCAL_DB="plataforma_db"
LOCAL_USER="postgres"

# 1. Baixar o Backup da Railway
echo "1. Baixando o Backup da Railway..."
pg_dump "$RAILWAY_URL" --no-owner --no-acl > "$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "Erro ao baixar o backup. Verifique a conexão ou a URL."
    exit 1
fi

# 2. Limpar o Banco Local (Reset)
echo "2. Resetando o Banco Local..."
docker compose exec -T db psql -U "$LOCAL_USER" -c "DROP DATABASE IF EXISTS $LOCAL_DB;"
docker compose exec -T db psql -U "$LOCAL_USER" -c "CREATE DATABASE $LOCAL_DB;"

# 3. Restaurar o Backup
echo "3. Restaurando o Backup..."
cat "$BACKUP_FILE" | docker compose exec -T db psql -U "$LOCAL_USER" -d "$LOCAL_DB"

# 4. Verificar os Dados
echo "4. Verificando os Dados..."
docker compose exec -T db psql -U "$LOCAL_USER" -d "$LOCAL_DB" -c "SELECT count(*) FROM django_migrations;"

# 5. Mover o banco para a pasta de backups
echo "5. Movendo o backup para $BACKUP_DIR..."
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Diretório $BACKUP_DIR não existe. Criando..."
    mkdir -p "$BACKUP_DIR"
fi
mv "$BACKUP_FILE" "$BACKUP_DIR/"

# 6. Rodar o Server
echo "6. Rodando o servidor..."
poetry run python manage.py runserver
