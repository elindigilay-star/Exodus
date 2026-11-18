from datetime import date, datetime
from decimal import Decimal

import pymysql
from flask import (Blueprint, jsonify, render_template, request, session)

from routes.auth import api_requerir_roles, requerir_roles

from . import modelo, servicio

nomina_bp = Blueprint('nomina', __name__, template_folder='templates', static_folder='static')

TIPOS_NOVEDAD = {'AUSENCIA', 'VACACIONES', 'PERMISO'}
ESTADOS_NOVEDAD = {'PENDIENTE', 'APROBADA', 'RECHAZADA'}


def _datos_json():
    """Las escrituras de la API solo aceptan JSON (protección CSRF)."""
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def _a_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _normalizar(fila):
    """Convierte Decimal y fechas a tipos serializables en JSON."""
    salida = {}
    for clave, valor in fila.items():
        if isinstance(valor, Decimal):
            salida[clave] = float(valor)
        elif isinstance(valor, datetime):
            salida[clave] = valor.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(valor, date):
            salida[clave] = valor.strftime('%Y-%m-%d')
        else:
            salida[clave] = valor
    return salida


def _normalizar_lista(filas):
    return [_normalizar(fila) for fila in filas]


# ---------------------------------------------------------------
# Vistas HTML
# ---------------------------------------------------------------

@nomina_bp.route('/modulo', methods=['GET'])
@requerir_roles('Administrador', 'Recursos Humanos')
def modulo():
    """Vista completa del módulo de nómina (empleados, calcular, novedades)."""
    return render_template('nomina/modulo.html')


@nomina_bp.route('/resumen', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_resumen_nomina():
    """Retorna el resumen de nómina en formato JSON."""
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    datos = modelo.obtener_resumen_nomina(f_inicio, f_fin)
    return jsonify({"estado": "exito", "data": datos}), 200


@nomina_bp.route('/ver-resumen', methods=['GET'])
@requerir_roles('Administrador', 'Recursos Humanos')
def ver_resumen_nomina_html():
    """Renderiza la vista HTML del resumen de nómina."""
    datos = modelo.obtener_resumen_nomina()
    return render_template('nomina/resumen.html', data=datos)


# ---------------------------------------------------------------
# RF-6 / RF-7: Empleados
# ---------------------------------------------------------------

@nomina_bp.route('/empleados', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_empleados():
    estado = request.args.get('estado')
    return jsonify(_normalizar_lista(modelo.listar_empleados(estado))), 200


@nomina_bp.route('/empleados', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_crear_empleado():
    datos = _datos_json()
    nombres = (datos.get('nombres') or '').strip()
    apellidos = (datos.get('apellidos') or '').strip()
    documento = (datos.get('documento') or '').strip()
    cargo = (datos.get('cargo') or '').strip()
    fecha_ingreso = (datos.get('fecha_ingreso') or '').strip()
    salario_base = _a_float(datos.get('salario_base'))

    if not nombres or not apellidos or not documento or not fecha_ingreso:
        return jsonify({
            'error': 'Faltan datos: nombres, apellidos, documento y fecha '
                     'de ingreso son obligatorios.',
        }), 422

    if salario_base is None or salario_base <= 0:
        return jsonify({'error': 'El salario base debe ser un número mayor a 0.'}), 422

    if modelo.obtener_empleado_por_documento(documento):
        return jsonify({'error': 'Ya existe un empleado registrado con ese documento.'}), 409

    id_empleado = modelo.crear_empleado(
        nombres, apellidos, documento, cargo or None,
        salario_base, fecha_ingreso,
        tipo_documento=(datos.get('tipo_documento') or 'CC').strip().upper(),
        email=(datos.get('email') or '').strip() or None,
        telefono=(datos.get('telefono') or '').strip() or None,
        direccion=(datos.get('direccion') or '').strip() or None,
        ciudad=(datos.get('ciudad') or '').strip() or None,
        tipo_contrato=(datos.get('tipo_contrato') or 'INDEFINIDO').strip().upper(),
        salario_integral=int(bool(datos.get('salario_integral'))),
        auxilio_transporte=_a_float(datos.get('auxilio_transporte')),
        riesgo_arl=int(datos.get('riesgo_arl') or 1),
        exonerado_salud=int(bool(datos.get('exonerado_salud'))),
        exonerado_parafiscales=int(bool(datos.get('exonerado_parafiscales'))),
        centro_costo=(datos.get('centro_costo') or '').strip() or None,
        banco=(datos.get('banco') or '').strip() or None,
        cuenta_banco=(datos.get('cuenta_banco') or '').strip() or None,
        dependientes=int(datos.get('dependientes') or 0),
    )
    return jsonify({
        'mensaje': 'Empleado registrado correctamente.',
        'id_empleado': id_empleado,
    }), 200


@nomina_bp.route('/empleados/actualizar', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_actualizar_empleado():
    """Actualiza datos laborales del empleado (contrato, ARL, exoneraciones)."""
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    if not id_empleado:
        return jsonify({'error': 'Falta el identificador del empleado.'}), 422
    if not modelo.obtener_empleado(id_empleado):
        return jsonify({'error': 'El empleado no existe.'}), 404

    campos = {}
    for clave in ('nombres', 'apellidos', 'cargo', 'email', 'telefono',
                  'direccion', 'ciudad', 'centro_costo', 'banco',
                  'cuenta_banco', 'tipo_contrato'):
        if clave in datos:
            campos[clave] = (datos.get(clave) or '').strip() or None
    if 'salario_base' in datos:
        salario = _a_float(datos.get('salario_base'))
        if salario is None or salario <= 0:
            return jsonify({'error': 'El salario base debe ser mayor a 0.'}), 422
        campos['salario_base'] = salario
    if 'auxilio_transporte' in datos:
        campos['auxilio_transporte'] = _a_float(datos.get('auxilio_transporte'))
    for clave in ('salario_integral', 'exonerado_salud', 'exonerado_parafiscales'):
        if clave in datos:
            campos[clave] = int(bool(datos.get(clave)))
    for clave in ('riesgo_arl', 'dependientes'):
        if clave in datos:
            campos[clave] = int(datos.get(clave) or 0)

    modelo.actualizar_empleado(id_empleado, **campos)
    return jsonify({'mensaje': 'Empleado actualizado correctamente.'}), 200


@nomina_bp.route('/empleados/eliminar', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_eliminar_empleado():
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    if not id_empleado:
        return jsonify({'error': 'Falta el identificador del empleado.'}), 422

    if not modelo.obtener_empleado(id_empleado):
        return jsonify({'error': 'El empleado no existe.'}), 404

    modelo.desactivar_empleado(id_empleado)
    return jsonify({'mensaje': 'Empleado eliminado correctamente.'}), 200


# ---------------------------------------------------------------
# RF-8: Calcular nómina
# ---------------------------------------------------------------

@nomina_bp.route('/calcular', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_calcular_nomina():
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    periodo = (datos.get('periodo') or '').strip()

    if not id_empleado or not periodo:
        return jsonify({
            'error': 'Faltan datos: selecciona un empleado y un periodo '
                     '(AAAA-MM).',
        }), 422

    empleado = modelo.obtener_empleado(id_empleado, solo_activo=True)
    if not empleado:
        return jsonify({'error': 'Empleado no encontrado o inactivo.'}), 404

    deducciones = modelo.listar_deducciones_activas()
    if not deducciones:
        return jsonify({'error': 'No existe configuración de deducciones. Cálculo detenido.'}), 409

    aportes = modelo.listar_aportes_activos()
    salario_base = float(empleado['salario_base'])

    total_deducciones = sum(salario_base * (float(d['porcentaje']) / 100) for d in deducciones)
    total_aportes = sum(salario_base * (float(a['porcentaje']) / 100) for a in aportes)
    salario_neto = salario_base - total_deducciones

    modelo.guardar_nomina(
        id_empleado, periodo, salario_base,
        round(total_deducciones, 2), round(total_aportes, 2), round(salario_neto, 2),
    )

    return jsonify({
        'mensaje': 'Nómina calculada correctamente.',
        'reporte': {
            'empleado': f"{empleado['nombres']} {empleado['apellidos']}",
            'periodo': periodo,
            'salario_base': round(salario_base, 2),
            'total_deducciones': round(total_deducciones, 2),
            'total_aportes_empleador': round(total_aportes, 2),
            'salario_neto': round(salario_neto, 2),
        },
    }), 200


@nomina_bp.route('/historial', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_historial_nomina():
    return jsonify(_normalizar_lista(modelo.listar_historial_nomina())), 200


# ---------------------------------------------------------------
# RF-9: Ausencias, vacaciones y permisos
# ---------------------------------------------------------------

@nomina_bp.route('/novedades', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_novedades():
    estado = request.args.get('estado')
    return jsonify(_normalizar_lista(modelo.listar_novedades(estado))), 200


@nomina_bp.route('/novedades', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_crear_novedad():
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    tipo = (datos.get('tipo') or '').strip().upper()
    fecha_inicio = (datos.get('fecha_inicio') or '').strip()
    fecha_fin = (datos.get('fecha_fin') or '').strip()
    motivo = (datos.get('motivo') or '').strip()

    if not id_empleado or not tipo or not fecha_inicio or not fecha_fin:
        return jsonify({
            'error': 'Faltan datos: empleado, tipo, fecha de inicio y fecha '
                     'de fin.',
        }), 422

    if tipo not in TIPOS_NOVEDAD:
        return jsonify({'error': 'Tipo de novedad no válido.'}), 422

    if fecha_fin < fecha_inicio:
        return jsonify({
            'error': 'La fecha de fin no puede ser anterior a la fecha de inicio.',
        }), 422

    if not modelo.obtener_empleado(id_empleado, solo_activo=True):
        return jsonify({'error': 'Empleado no encontrado o inactivo.'}), 404

    if modelo.existe_novedad_cruzada(id_empleado, fecha_inicio, fecha_fin):
        return jsonify({'error': 'El empleado ya tiene una solicitud en esas fechas.'}), 409

    id_novedad = modelo.crear_novedad(
        id_empleado, tipo, fecha_inicio, fecha_fin, motivo or None,
    )
    return jsonify({
        'mensaje': 'Solicitud registrada correctamente.',
        'id_novedad': id_novedad,
    }), 200


@nomina_bp.route('/novedades/estado', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_actualizar_novedad():
    datos = _datos_json()
    id_novedad = datos.get('id_novedad')
    estado = (datos.get('estado') or '').strip().upper()

    if not id_novedad or not estado:
        return jsonify({'error': 'Faltan datos: identificador y estado.'}), 422

    if estado not in ESTADOS_NOVEDAD:
        return jsonify({'error': 'Estado no válido.'}), 422

    if modelo.actualizar_estado_novedad(id_novedad, estado) == 0:
        return jsonify({'error': 'Solicitud no encontrada.'}), 404

    return jsonify({'mensaje': 'Estado actualizado correctamente.'}), 200


# ---------------------------------------------------------------
# Motor de liquidación: parámetros, periodos, novedades y colilla
# ---------------------------------------------------------------

def _error_nomina(error):
    """Respuesta JSON uniforme para errores del motor de nómina."""
    if isinstance(error, pymysql.MySQLError):
        print(f"AVISO: error de base de datos en nómina: {error}")
        return jsonify({
            'error': 'No se pudo consultar la base de datos de nómina.',
        }), 500
    return jsonify({'error': str(error)}), 400


@nomina_bp.route('/parametros', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_parametros():
    """Lista los parámetros legales editables (SMMLV, UVT, tasas...)."""
    try:
        return jsonify({
            'estado': 'exito',
            'data': servicio.listar_parametros(),
            'calculados': servicio.obtener_parametros(),
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/parametros', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_actualizar_parametros():
    """Actualiza uno o varios parámetros legales de nómina."""
    datos = _datos_json()
    cambios = datos.get('parametros', datos)
    try:
        actualizados = servicio.actualizar_parametros(cambios)
        return jsonify({
            'mensaje': f'{actualizados} parámetro(s) actualizado(s).',
            'data': servicio.obtener_parametros(),
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/conceptos', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_conceptos():
    """Catálogo de conceptos de nómina con su cuenta PUC."""
    try:
        return jsonify({
            'estado': 'exito',
            'data': servicio.listar_conceptos(),
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/periodos', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_periodos():
    """Historial de periodos de nómina liquidados."""
    try:
        return jsonify({
            'estado': 'exito',
            'data': servicio.listar_periodos(request.args.get('limite', 50)),
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/periodos/liquidar', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_liquidar_periodo():
    """Calcula y guarda la nómina de un rango de fechas."""
    datos = _datos_json()
    try:
        resultado = servicio.liquidar_periodo(
            fecha_inicio=datos.get('fecha_inicio'),
            fecha_fin=datos.get('fecha_fin'),
            tipo=datos.get('tipo') or 'MENSUAL',
            nombre=datos.get('nombre') or None,
            id_usuario=session.get('usuario_id'),
            id_empleado=datos.get('id_empleado') or None,
        )
        return jsonify({
            'mensaje': 'Nómina liquidada correctamente.',
            'data': resultado,
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/periodos/<int:id_periodo>', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_obtener_periodo(id_periodo):
    """Detalle de un periodo con el desglose por empleado y concepto."""
    try:
        periodo = servicio.obtener_periodo(id_periodo)
        if not periodo:
            return jsonify({'error': 'Periodo no encontrado.'}), 404
        return jsonify({'estado': 'exito', 'data': periodo}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/periodos/<int:id_periodo>/contabilizar', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_contabilizar_periodo(id_periodo):
    """Genera el comprobante contable de nómina del periodo."""
    try:
        resultado = servicio.contabilizar_periodo(
            id_periodo, id_usuario=session.get('usuario_id')
        )
        return jsonify({
            'mensaje': 'Nómina contabilizada correctamente.',
            'data': resultado,
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/periodos/<int:id_periodo>/colilla/<int:id_empleado>', methods=['GET'])
@requerir_roles('Administrador', 'Recursos Humanos')
def ver_colilla(id_periodo, id_empleado):
    """Colilla de pago imprimible de un empleado en un periodo."""
    periodo = servicio.obtener_periodo(id_periodo)
    if not periodo:
        return 'Periodo no encontrado.', 404
    detalle = next(
        (d for d in periodo['detalles'] if int(d['id_empleado']) == int(id_empleado)),
        None,
    )
    if not detalle:
        return 'El empleado no hace parte de este periodo.', 404
    return render_template('nomina/colilla.html', periodo=periodo, detalle=detalle)


@nomina_bp.route('/novedades-nomina', methods=['GET'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_listar_novedades_nomina():
    """Lista horas extras, bonificaciones y deducciones del motor."""
    try:
        return jsonify({
            'estado': 'exito',
            'data': servicio.listar_novedades_nomina(
                id_empleado=request.args.get('id_empleado') or None,
                estado=request.args.get('estado', 'ACTIVA') or None,
                fecha_inicio=request.args.get('fecha_inicio'),
                fecha_fin=request.args.get('fecha_fin'),
            ),
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/novedades-nomina', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_crear_novedad_nomina():
    """Registra una hora extra, bonificación o deducción para el periodo."""
    datos = _datos_json()
    try:
        id_novedad = servicio.crear_novedad_nomina(
            id_empleado=datos.get('id_empleado'),
            concepto_codigo=datos.get('concepto_codigo'),
            fecha=datos.get('fecha'),
            cantidad=datos.get('cantidad') or 0,
            valor_unitario=datos.get('valor_unitario'),
            valor_total=datos.get('valor_total'),
            descripcion=datos.get('descripcion'),
            aplica_ibc=datos.get('aplica_ibc'),
            aplica_retencion=datos.get('aplica_retencion'),
            id_usuario=session.get('usuario_id'),
        )
        return jsonify({
            'mensaje': 'Novedad registrada correctamente.',
            'id_novedad_nomina': id_novedad,
        }), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


@nomina_bp.route('/novedades-nomina/anular', methods=['POST'])
@api_requerir_roles('Administrador', 'Recursos Humanos')
def api_anular_novedad_nomina():
    """Anula una novedad del motor de nómina."""
    datos = _datos_json()
    try:
        servicio.anular_novedad_nomina(
            datos.get('id_novedad_nomina') or datos.get('id_novedad'),
            id_usuario=session.get('usuario_id'),
        )
        return jsonify({'mensaje': 'Novedad anulada.'}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_nomina(error)


# ---------------- Enlace con la aplicación ----------------

def registrar_nomina(app):
    """Registra el blueprint y prepara las tablas. Se llama una vez desde app.py.

    Se monta en /api/nomina:
      - vista:  /api/nomina/modulo
      - API:    /api/nomina/empleados, /calcular, /novedades, ...
      - static: /api/nomina/static/css/nomina.css, .../js/nomina.js
    """
    app.register_blueprint(nomina_bp, url_prefix='/api/nomina')
    try:
        modelo.crear_tablas_nomina()
    except (pymysql.MySQLError, OSError, ValueError) as error:
        print(f"AVISO: no se pudieron preparar las tablas de nómina: {error}")
