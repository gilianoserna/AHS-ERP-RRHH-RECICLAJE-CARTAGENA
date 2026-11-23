# Despliegue de pruebas en la VM de Oracle Cloud

1. En GitHub, Settings → Secrets and variables → Actions, crear `ORACLE_HOST`,
   `ORACLE_USER` y `ORACLE_SSH_KEY` (contenido de la llave privada).
2. Actions → «Desplegar en VM Oracle (pruebas)» → Run workflow. Copia el código
   a `~/ash_rrhh` en la VM y corre `deploy/desplegar.sh` (instala Docker si falta,
   genera credenciales en `deploy/.env`, crea la base `ash_rrhh_pruebas` e
   instala los módulos). Nada se instala en el PC.
3. Desde el PC, abrir un túnel y entrar por el navegador:

   ```
   ssh -i <llave> -L 8069:127.0.0.1:8069 <usuario>@<ip-de-la-vm>
   ```
   Luego <http://localhost:8069>, usuario `admin`, contraseña `ADMIN_PASSWORD` de `deploy/.env`.

4. Gestión de empleados → Configuración → Conexión con Alegra: crear la
   conexión en modo **Ensayo**; como administrador escribir el correo y el
   token de Alegra; «Probar conexión»; pasar a **Real**.

Odoo no queda expuesto a internet: solo escucha en 127.0.0.1 de la VM.
Para actualizar después de cambios en el código: volver a correr `desplegar.sh`.
