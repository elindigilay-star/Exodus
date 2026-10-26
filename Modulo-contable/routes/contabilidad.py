from flask import Blueprint, request, jsonify, render_template, send_file
from services.estado_resultados_service import generar_estado_resultados
from services.gasto_service import (
    registrar_gasto_deducible, listar_gastos_deducibles, obtener_gasto_deducible,
    editar_gasto_deducible, anular_gasto_deducible
)
from services.consolidacion_service import consolidar_informacion_contable
from services.balance_service import calcular_balance_general
from services.reporte_service import (
    exportar_estado_resultados_pdf, exportar_estado_resultados_excel,
    exportar_balance_general_pdf, exportar_balance_general_excel,
    exportar_consolidado_pdf, exportar_consolidado_excel,
    obtener_estado_resultados_con_periodo, obtener_balance_con_periodo,
    obtener_consolidado_con_periodo
)
from flask import session
from routes.auth import login_requerido, requerir_roles

contabilidad_bp = Blueprint('contabilidad', __name__)


def fecha_a_texto(valor):
    """Convierte la fecha a texto sin importar si llega como str o como date/datetime."""
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor  # ya es texto
    return valor.strftime('%Y-%m-%d %H:%M:%S')


# CU-01: Estado de Resultados
@contabilidad_bp.route('/estado-resultados', methods=['GET'])
def api_estado_resultados():
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        resultado = generar_estado_resultados(f_inicio, f_fin)
        return jsonify({"estado": "exito", "data": resultado}), 200
    except ValueError as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-02: Registrar Gastos Deducibles (Restringido a Contador y Administrador)
@contabilidad_bp.route('/gastos', methods=['POST'])
@requerir_roles('Contador', 'Administrador')
def api_registrar_gasto():
    try:
        datos = request.get_json() or {}
        id_usuario = session.get('usuario_id')
        respuesta = registrar_gasto_deducible(
            descripcion=datos.get('descripcion'),
            monto=datos.get('monto'),
            id_usuario=id_usuario,
            categoria=datos.get('categoria'),
            tercero=datos.get('tercero'),
            nit=datos.get('nit'),
            numero_documento=datos.get('numero_documento'),
            fecha=datos.get('fecha')
        )
        return jsonify({"estado": "exito", "data": respuesta}), 201
    except (ValueError, PermissionError) as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-02b: Listar gastos deducibles
@contabilidad_bp.route('/gastos', methods=['GET'])
@login_requerido
def api_listar_gastos():
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        estado = request.args.get('estado', 'ACTIVO')
        gastos = listar_gastos_deducibles(fecha_inicio=f_inicio, fecha_fin=f_fin, estado_gasto=estado)
        # Convertir fechas a string para JSON serializable
        resultado = []
        for g in gastos:
            item = dict(g)
            item['fecha'] = fecha_a_texto(item.get('fecha'))
            resultado.append(item)
        return jsonify({"estado": "exito", "data": resultado}), 200
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-02c: Obtener un gasto para editar
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['GET'])
@login_requerido
def api_obtener_gasto(id_gasto):
    try:
        gasto = obtener_gasto_deducible(id_gasto)
        if not gasto:
            return jsonify({"estado": "error", "mensaje": "Gasto no encontrado."}), 404
        item = dict(gasto)
        item['fecha'] = fecha_a_texto(item.get('fecha'))
        return jsonify({"estado": "exito", "data": item}), 200
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-02d: Editar un gasto deducible
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['PUT'])
@requerir_roles('Contador', 'Administrador')
def api_editar_gasto(id_gasto):
    try:
        datos = request.get_json() or {}
        respuesta = editar_gasto_deducible(
            id_gasto=id_gasto,
            descripcion=datos.get('descripcion'),
            monto=datos.get('monto'),
            categoria=datos.get('categoria'),
            tercero=datos.get('tercero'),
            nit=datos.get('nit'),
            numero_documento=datos.get('numero_documento'),
            fecha=datos.get('fecha')
        )
        return jsonify({"estado": "exito", "data": respuesta}), 200
    except (ValueError, PermissionError) as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-02e: Anular un gasto deducible
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['DELETE'])
@requerir_roles('Contador', 'Administrador')
def api_anular_gasto(id_gasto):
    try:
        respuesta = anular_gasto_deducible(id_gasto)
        return jsonify({"estado": "exito", "data": respuesta}), 200
    except ValueError as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-03: Consolidar Información Contable
@contabilidad_bp.route('/consolidado', methods=['GET'])
def api_consolidar():
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    consolidado = consolidar_informacion_contable(f_inicio, f_fin)
    return jsonify({"estado": "exito", "data": consolidado}), 200

# CU-04: Balance General
@contabilidad_bp.route('/balance-general', methods=['GET'])
def api_balance_general():
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        balance = calcular_balance_general(f_inicio, f_fin)
        return jsonify({"estado": "exito", "data": balance}), 200
    except ValueError as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400

# CU-05: Exportar Reportes (PDF / Excel)
@contabilidad_bp.route('/exportar-reporte', methods=['GET'])
def api_exportar_reporte():
    tipo = request.args.get('tipo', 'estado_resultados').lower()  # estado_resultados | balance | consolidado
    formato = request.args.get('formato', 'pdf').lower()
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        if tipo == 'balance':
            datos, periodo_txt = obtener_balance_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_balance_general_pdf(datos, periodo_txt)
                nombre = 'balance_general.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_balance_general_excel(datos, periodo_txt)
                nombre = 'balance_general.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return jsonify({"estado": "error", "mensaje": "Formato no soportado. Use 'pdf' o 'excel'."}), 400
        elif tipo == 'consolidado':
            datos, periodo_txt = obtener_consolidado_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_consolidado_pdf(datos, periodo_txt)
                nombre = 'consolidado_contable.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_consolidado_excel(datos, periodo_txt)
                nombre = 'consolidado_contable.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return jsonify({"estado": "error", "mensaje": "Formato no soportado. Use 'pdf' o 'excel'."}), 400
        else:  # estado_resultados
            datos, periodo_txt = obtener_estado_resultados_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_estado_resultados_pdf(datos, periodo_txt)
                nombre = 'estado_resultados.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_estado_resultados_excel(datos, periodo_txt)
                nombre = 'estado_resultados.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return jsonify({"estado": "error", "mensaje": "Formato no soportado. Use 'pdf' o 'excel'."}), 400

        return send_file(stream, mimetype=mime, as_attachment=True, download_name=nombre)
    except ValueError as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400


# Rutas de renderizado HTML
AVISO_SIN_DATOS = "Aún no hay movimientos registrados (ventas de inventario, nómina o gastos). Mostrando valores en cero."


@contabilidad_bp.route('/ver-estado-resultados', methods=['GET'])
@login_requerido
def ver_estado_resultados_html():
    aviso = None
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        datos = generar_estado_resultados(f_inicio, f_fin)
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {'ingresos_totales': 0.0, 'costo_ventas': 0.0, 'utilidad_bruta': 0.0,
                 'gastos_operativos': 0.0,
                 'desglose_gastos': {'nomina': 0.0, 'gastos_deducibles': 0.0, 'perdidas_inventario': 0.0},
                 'utilidad_neta': 0.0}
    return render_template('contabilidad/estado_resultados.html',
                           data=datos, aviso=aviso, fecha_inicio=f_inicio, fecha_fin=f_fin)


@contabilidad_bp.route('/ver-balance-general', methods=['GET'])
@login_requerido
def ver_balance_general_html():
    aviso = None
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        datos = calcular_balance_general(f_inicio, f_fin)
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {'activos': {'efectivo_caja': 0.0, 'inventario': 0.0, 'total_activos': 0.0},
                 'pasivos': {'pasivos_laborales': 0.0, 'total_pasivos': 0.0},
                 'patrimonio': {'utilidad_ejercicio': 0.0, 'total_patrimonio': 0.0}}
    return render_template('contabilidad/balance_general.html',
                           data=datos, aviso=aviso, fecha_inicio=f_inicio, fecha_fin=f_fin)


@contabilidad_bp.route('/ver-registrar-gasto', methods=['GET'])
@login_requerido
def ver_registrar_gasto_html():
    return render_template('contabilidad/registrar_gasto.html')


@contabilidad_bp.route('/ver-listar-gastos', methods=['GET'])
@login_requerido
def ver_listar_gastos_html():
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    return render_template('contabilidad/listar_gastos.html',
                           fecha_inicio=f_inicio, fecha_fin=f_fin)