from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, render_template, request

from . import modelo
from routes.auth import login_requerido

nomina_bp = Blueprint('nomina', __name__, template_folder='templates', static_folder='static')

TIPOS_NOVEDAD = {'AUSENCIA', 'VACACIONES', 'PERMISO'}
ESTADOS_NOVEDAD = {'PENDIENTE', 'APROBADA', 'RECHAZADA'}


def _datos_json():
    return request.get_json(silent=True) or request.form


def _a_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _normalizar(fila):
    """Convierte Decimal y fechas a tipos que el JSON representa igual que en PHP."""
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
@login_requerido
def modulo():
    """Vista completa del módulo de nómina (empleados, calcular, novedades)."""
    return render_template('nomina/modulo.html')


@nomina_bp.route('/resumen', methods=['GET'])
def api_resumen_nomina():
    """Retorna el resumen de nómina en formato JSON."""
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    datos = modelo.obtener_resumen_nomina(f_inicio, f_fin)
    return jsonify({"estado": "exito", "data": datos}), 200


@nomina_bp.route('/ver-resumen', methods=['GET'])
@login_requerido
def ver_resumen_nomina_html():
    """Renderiza la vista HTML del resumen de nómina."""
    datos = modelo.obtener_resumen_nomina()
    return render_template('nomina/resumen.html', data=datos)


# ---------------------------------------------------------------
# RF-6 / RF-7: Empleados
# ---------------------------------------------------------------

@nomina_bp.route('/empleados', methods=['GET'])
def api_listar_empleados():
    estado = request.args.get('estado')
    return jsonify(_normalizar_lista(modelo.listar_empleados(estado))), 200


@nomina_bp.route('/empleados', methods=['POST'])
def api_crear_empleado():
    datos = _datos_json()
    nombres = (datos.get('nombres') or '').strip()
    apellidos = (datos.get('apellidos') or '').strip()
    documento = (datos.get('documento') or '').strip()
    cargo = (datos.get('cargo') or '').strip()
    fecha_ingreso = (datos.get('fecha_ingreso') or '').strip()
    salario_base = _a_float(datos.get('salario_base'))

    if not nombres or not apellidos or not documento or not fecha_ingreso:
        return jsonify({'error': 'Faltan datos: nombres, apellidos, documento y fecha de ingreso son obligatorios.'}), 422

    if salario_base is None or salario_base <= 0:
        return jsonify({'error': 'El salario base debe ser un número mayor a 0.'}), 422

    if modelo.obtener_empleado_por_documento(documento):
        return jsonify({'error': 'Ya existe un empleado registrado con ese documento.'}), 409

    id_empleado = modelo.crear_empleado(nombres, apellidos, documento, cargo or None, salario_base, fecha_ingreso)
    return jsonify({'mensaje': 'Empleado registrado correctamente.', 'id_empleado': id_empleado}), 200


@nomina_bp.route('/empleados/eliminar', methods=['POST'])
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
def api_calcular_nomina():
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    periodo = (datos.get('periodo') or '').strip()

    if not id_empleado or not periodo:
        return jsonify({'error': 'Faltan datos: selecciona un empleado y un periodo (AAAA-MM).'}), 422

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
def api_historial_nomina():
    return jsonify(_normalizar_lista(modelo.listar_historial_nomina())), 200


# ---------------------------------------------------------------
# RF-9: Ausencias, vacaciones y permisos
# ---------------------------------------------------------------

@nomina_bp.route('/novedades', methods=['GET'])
def api_listar_novedades():
    estado = request.args.get('estado')
    return jsonify(_normalizar_lista(modelo.listar_novedades(estado))), 200


@nomina_bp.route('/novedades', methods=['POST'])
def api_crear_novedad():
    datos = _datos_json()
    id_empleado = datos.get('id_empleado')
    tipo = (datos.get('tipo') or '').strip().upper()
    fecha_inicio = (datos.get('fecha_inicio') or '').strip()
    fecha_fin = (datos.get('fecha_fin') or '').strip()
    motivo = (datos.get('motivo') or '').strip()

    if not id_empleado or not tipo or not fecha_inicio or not fecha_fin:
        return jsonify({'error': 'Faltan datos: empleado, tipo, fecha de inicio y fecha de fin.'}), 422

    if tipo not in TIPOS_NOVEDAD:
        return jsonify({'error': 'Tipo de novedad no válido.'}), 422

    if fecha_fin < fecha_inicio:
        return jsonify({'error': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}), 422

    if not modelo.obtener_empleado(id_empleado, solo_activo=True):
        return jsonify({'error': 'Empleado no encontrado o inactivo.'}), 404

    if modelo.existe_novedad_cruzada(id_empleado, fecha_inicio, fecha_fin):
        return jsonify({'error': 'El empleado ya tiene una solicitud en esas fechas.'}), 409

    id_novedad = modelo.crear_novedad(id_empleado, tipo, fecha_inicio, fecha_fin, motivo or None)
    return jsonify({'mensaje': 'Solicitud registrada correctamente.', 'id_novedad': id_novedad}), 200


@nomina_bp.route('/novedades/estado', methods=['POST'])
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
    except Exception as error:  # La app arranca aunque la base de datos esté apagada
        print(f"AVISO: no se pudieron preparar las tablas de nómina: {error}")
