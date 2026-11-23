# Integración con Alegra

## Qué viaja

| Dirección | Qué | Cuándo |
|---|---|---|
| Alegra → ERP | Empleados (documento, nombre, correo, teléfono, cargo, centro de costo, ingreso/retiro) | Cron diario (desactivado hasta configurar) o botón «Traer empleados ahora» |
| ERP → Alegra | Novedades de un periodo **aprobado**: horas extra, recargos, vacaciones, incapacidades, licencias, ausencias | Botón «Enviar a Alegra» del periodo |

## API

Confirmado de la API pública de Alegra (<https://developer.alegra.com>):

- URL base `https://api.alegra.com/api/v1`.
- Autenticación básica con **correo + token** (Alegra → Configuración → Integraciones/API).
- Paginación `start` / `limit` (máximo 30).
- Límite de peticiones por minuto: el cliente reintenta con espera creciente ante 429.

**Por confirmar con la cuenta de la empresa antes de pasar a Real:** las rutas
exactas de nómina (empleados y novedades) y los nombres de campo del JSON.
Están en la pantalla de conexión (`ruta_empleados`, `ruta_novedades`) y en
`addons/ash_alegra_conector/lib/mapeo.py` (`MAPA_EMPLEADO_POR_DEFECTO`,
`novedad_a_alegra`), de modo que ajustarlas no toca la lógica.

## Puesta en marcha

1. Configuración → Conexión con Alegra: crear la conexión en **modo Ensayo**.
2. Configuración → Conceptos de Alegra: poner el código de cada concepto tal
   como existe en la nómina de Alegra (los que trae son de ejemplo).
3. Como administrador, escribir correo y token; «Probar conexión».
4. Pasar a **Real**, «Traer empleados ahora» y revisar la bitácora (creados,
   actualizados, sin cambios, ausentes, errores).
5. Activar el cron «ASH RRHH: traer empleados de Alegra».
6. Primer periodo: calcular, aprobar, **descargar CSV** y compararlo con lo
   que espera Alegra; luego usar «Enviar a Alegra».

## Garantías

- **Idempotencia:** cada empleado guarda la huella de lo último leído; si no
  cambió, no se escribe.
- **Sin borrados automáticos:** quien deja de venir de Alegra se reporta como
  «ausente»; archivar retirados es una opción explícita.
- **Envío por línea:** cada novedad guarda su estado, el ID que devolvió Alegra
  o el error; reenviar solo manda las pendientes o fallidas.
- **Respaldo CSV:** si la cuenta no expone novedades por API, el CSV
  (`;`, UTF-8 con BOM) se carga a mano en Alegra.
