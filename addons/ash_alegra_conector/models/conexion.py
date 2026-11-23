# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..lib import alegra_client, mapeo

_logger = logging.getLogger(__name__)


class AshAlegraConexion(models.Model):
    _name = 'ash.alegra.conexion'
    _description = 'Conexión con la API de Alegra'

    name = fields.Char(required=True, default='Alegra nómina')
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company)
    active = fields.Boolean(default=True)
    modo = fields.Selection([('ensayo', 'Ensayo (sin red)'), ('real', 'Real')], default='ensayo',
                            required=True,
                            help='En ensayo no se llama a Alegra: sirve para probar el flujo completo.')
    correo = fields.Char('Correo de Alegra', groups='base.group_system')
    token = fields.Char('Token de la API', groups='base.group_system',
                        help='Alegra > Configuración > Integraciones / API. Nunca se muestra en la bitácora.')
    url_base = fields.Char(default=alegra_client.URL_BASE, required=True)
    ruta_empleados = fields.Char(default=alegra_client.RUTAS_POR_DEFECTO['empleados'], required=True)
    ruta_novedades = fields.Char(default=alegra_client.RUTAS_POR_DEFECTO['novedades'], required=True)
    sincronizar_empleados = fields.Boolean('Traer empleados a diario', default=True)
    archivar_retirados = fields.Boolean(
        'Archivar retirados', default=False,
        help='Si Alegra marca al empleado como retirado, archivarlo aquí. Si no, solo se informa.')
    ultima_sincronizacion = fields.Datetime(readonly=True)
    bitacora_ids = fields.One2many('ash.alegra.bitacora', 'conexion_id', string='Bitácora')

    _ash_una_por_compania = models.Constraint('UNIQUE(company_id)', 'Ya hay una conexión para esta compañía.')

    def _cliente(self, datos_ensayo=None):
        self.ensure_one()
        rutas = {'empleados': self.ruta_empleados, 'novedades': self.ruta_novedades}
        if self.modo == 'ensayo':
            return alegra_client.ClienteAlegra(alegra_client.TransporteFalso(datos_ensayo or {}), rutas)
        conexion = self.sudo()
        if not (conexion.correo and conexion.token):
            raise UserError(_('Configure el correo y el token de Alegra.'))
        transporte = alegra_client.TransporteHttp(conexion.correo, conexion.token, url_base=self.url_base)
        return alegra_client.ClienteAlegra(transporte, rutas)

    def _registrar(self, operacion, resultado, **detalle):
        return self.env['ash.alegra.bitacora'].sudo().create(
            dict(conexion_id=self.id, operacion=operacion, resultado=resultado, **detalle))

    def action_probar(self):
        self.ensure_one()
        try:
            self._cliente().probar_conexion()
        except alegra_client.ErrorAlegra as e:
            self._registrar('prueba', 'error', errores=str(e))
            raise UserError(_('Alegra no respondió bien: %s', e)) from None
        self._registrar('prueba', 'ok')
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'type': 'success', 'message': _('Conexión con Alegra correcta.')}}

    # ------------------------------------------------------------------ empleados
    def action_sincronizar_empleados(self, datos_ensayo=None):
        for conexion in self:
            conexion._sincronizar_empleados(datos_ensayo)

    def _sincronizar_empleados(self, datos_ensayo=None):
        self.ensure_one()
        Empleado = self.env['hr.employee'].sudo().with_context(active_test=False)
        if isinstance(datos_ensayo, list):  # en ensayo: lista de empleados «de Alegra»
            datos_ensayo = {self.ruta_empleados: datos_ensayo}
        try:
            registros = self._cliente(datos_ensayo).empleados()
        except alegra_client.ErrorAlegra as e:
            return self._registrar('empleados', 'error', errores=str(e))
        normalizados, errores = [], []
        for registro in registros:
            try:
                normalizados.append(mapeo.empleado(registro))
            except mapeo.ErrorMapeo as e:
                errores.append(str(e))
        existentes = Empleado.search([('company_id', '=', self.company_id.id), ('ash_id_alegra', '!=', False)])
        plan = mapeo.plan_sincronizacion(normalizados, {e.ash_id_alegra: e.ash_huella_alegra or ''
                                                         for e in existentes})
        ahora = fields.Datetime.now()
        por_id = {e.ash_id_alegra: e for e in existentes}
        for datos, huella in plan['crear']:
            # Empleado creado a mano antes de conectar: se enlaza por documento.
            previo = Empleado.search([('company_id', '=', self.company_id.id), ('ash_id_alegra', '=', False),
                                      ('ash_numero_documento', '=', datos['numero_documento'])], limit=1)
            valores = self._valores_empleado(datos, huella, ahora)
            if previo:
                previo.write(valores)
            else:
                Empleado.create(dict(valores, company_id=self.company_id.id))
        for datos, huella in plan['actualizar']:
            por_id[datos['id_alegra']].write(self._valores_empleado(datos, huella, ahora))
        self.ultima_sincronizacion = ahora
        return self._registrar(
            'empleados', 'error' if errores else 'ok', creados=len(plan['crear']),
            actualizados=len(plan['actualizar']), sin_cambios=len(plan['sin_cambios']),
            ausentes=', '.join(plan['ausentes']), errores='\n'.join(errores))

    def _valores_empleado(self, datos, huella, ahora):
        valores = {
            'name': datos['nombre'], 'ash_id_alegra': datos['id_alegra'],
            'ash_tipo_documento': datos['tipo_documento'], 'ash_numero_documento': datos['numero_documento'],
            'ash_centro_costo': datos['centro_costo'], 'ash_huella_alegra': huella,
            'ash_sincronizado_el': ahora,
        }
        if datos['correo']:
            valores['work_email'] = datos['correo']
        if datos['telefono']:
            valores['mobile_phone'] = datos['telefono']
        if datos['cargo']:
            valores['job_title'] = datos['cargo']
        if self.archivar_retirados:
            valores['active'] = datos['activo']
        return valores

    @api.model
    def _cron_sincronizar(self):
        for conexion in self.search([('sincronizar_empleados', '=', True)]):
            try:
                conexion._sincronizar_empleados()
                self.env.cr.commit()  # una compañía con error no deshace a las demás
            except Exception:  # noqa: BLE001
                self.env.cr.rollback()
                _logger.exception('Fallo sincronizando empleados de Alegra (%s)', conexion.company_id.name)

    # ------------------------------------------------------------------ novedades
    def enviar_periodo(self, periodo):
        self.ensure_one()
        cliente = self._cliente()
        conceptos = self.env['ash.novedad.concepto'].search(
            [('company_id', 'in', (periodo.company_id.id, False))])
        codigos = {c.clave: c.codigo_alegra for c in conceptos}
        enviados = fallidos = 0
        for linea in periodo.linea_ids.filtered(lambda l: l.estado_envio != 'enviado'):
            id_empleado = linea.employee_id.sudo().ash_id_alegra
            try:
                if not id_empleado:
                    raise mapeo.ErrorMapeo(_('El empleado no está enlazado con Alegra.'))
                cuerpo = mapeo.novedad_a_alegra({
                    'concepto': linea.concepto, 'cantidad': linea.cantidad,
                    'periodo_desde': periodo.fecha_desde, 'periodo_hasta': periodo.fecha_hasta,
                    'fecha_inicio': linea.fecha_inicio, 'fecha_fin': linea.fecha_fin,
                    'observacion': linea.observacion}, id_empleado, codigos)
                respuesta = cliente.enviar_novedad(cuerpo) or {}
                linea.write({'estado_envio': 'enviado', 'error_envio': False,
                             'id_alegra': str(respuesta.get('id') or '')})
                enviados += 1
            except (alegra_client.ErrorAlegra, mapeo.ErrorMapeo) as e:
                linea.write({'estado_envio': 'error', 'error_envio': str(e)})
                fallidos += 1
        self._registrar('novedades', 'error' if fallidos else 'ok', creados=enviados,
                        errores=_('%s líneas con error en %s', fallidos, periodo.name) if fallidos else False)
        return enviados, fallidos


class AshAlegraBitacora(models.Model):
    _name = 'ash.alegra.bitacora'
    _description = 'Bitácora del conector Alegra'
    _order = 'create_date desc'

    conexion_id = fields.Many2one('ash.alegra.conexion', required=True, ondelete='cascade')
    operacion = fields.Selection([('prueba', 'Prueba de conexión'), ('empleados', 'Empleados'),
                                  ('novedades', 'Novedades')], required=True)
    resultado = fields.Selection([('ok', 'Correcto'), ('error', 'Con errores')], required=True)
    creados = fields.Integer()
    actualizados = fields.Integer()
    sin_cambios = fields.Integer()
    ausentes = fields.Text(help='IDs que están en el ERP pero ya no llegan de Alegra (revisar).')
    errores = fields.Text()
