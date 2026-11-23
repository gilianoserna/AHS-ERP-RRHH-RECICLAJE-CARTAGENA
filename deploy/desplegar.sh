#!/usr/bin/env bash
# Despliega ASH RRHH (Odoo 19 Community + addons) en una VM Linux con Docker.
# Uso (en la VM, dentro de la carpeta del proyecto):  bash deploy/desplegar.sh
# Es idempotente: si ya está desplegado, actualiza los módulos.
set -euo pipefail
cd "$(dirname "$0")"
BASE=ash_rrhh_pruebas
MODULOS=ash_alegra_conector

if ! command -v docker >/dev/null 2>&1; then
  echo ">> Instalando Docker"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi
DOCKER="docker"; docker info >/dev/null 2>&1 || DOCKER="sudo docker"

if [ ! -f .env ]; then
  echo ">> Generando credenciales locales (.env, solo en esta VM)"
  umask 077
  {
    echo "PG_PASSWORD=$(openssl rand -hex 16)"
    echo "ADMIN_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=')"
    echo "MASTER_PASSWORD=$(openssl rand -hex 16)"
    echo "ODOO_PUERTO=8069"
  } > .env
fi
set -a; . ./.env; set +a

umask 077
cat > odoo.conf <<CONF
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
db_host = db
db_user = odoo
db_password = ${PG_PASSWORD}
admin_passwd = ${MASTER_PASSWORD}
list_db = False
proxy_mode = False
without_demo = True
CONF
chmod 644 odoo.conf

$DOCKER compose up -d db
sleep 8
if $DOCKER compose run --rm odoo psql "postgresql://odoo:${PG_PASSWORD}@db/postgres" -tAc \
     "SELECT 1 FROM pg_database WHERE datname='${BASE}'" 2>/dev/null | grep -q 1; then
  echo ">> Actualizando módulos en ${BASE}"
  $DOCKER compose run --rm odoo odoo --config=/etc/odoo/odoo.conf -d "$BASE" -u "$MODULOS" --stop-after-init
else
  echo ">> Creando base ${BASE} e instalando ${MODULOS}"
  $DOCKER compose run --rm odoo odoo --config=/etc/odoo/odoo.conf -d "$BASE" -i "$MODULOS" \
    --load-language=es_CO --stop-after-init
  echo ">> Fijando contraseña del administrador"
  $DOCKER compose run --rm -T odoo odoo shell --config=/etc/odoo/odoo.conf -d "$BASE" --no-http <<PY
env.ref('base.user_admin').write({'password': '${ADMIN_PASSWORD}', 'lang': 'es_CO', 'tz': 'America/Bogota'})
env.company.write({'country_id': env.ref('base.co').id})
env.cr.commit()
PY
fi
$DOCKER compose up -d odoo
sleep 5
curl -fsS -o /dev/null "http://127.0.0.1:${ODOO_PUERTO}/web/login" && echo ">> Odoo responde en 127.0.0.1:${ODOO_PUERTO}"
echo ">> Listo. Base: ${BASE}  Usuario: admin  Contraseña: ver ADMIN_PASSWORD en $(pwd)/.env"
