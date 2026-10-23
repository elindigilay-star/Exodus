from flask import Blueprint, request, jsonify, render_template, send_file
from services.estado_resultados_service import generar_estado_resultados
from services.gasto_service import registrar_gasto_deducible
from services.consolidacion_service import consolidar_informacion_contable
from services.balance_service import calcular_balance_general
from services.reporte_service import exportar_estado_resultados_pdf, exportar_estado_resultados_excel
from flask import session
from routes.auth import login_requerido, requerir_roles

contabilidad_bp = Blueprint('contabilidad', __name__)

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
        id_usuario = session.get('usuario_id')  # siempre el usuario con sesión activa
        respuesta = registrar_gasto_deducible(
            descripcion=datos.get('descripcion'),
            monto=datos.get('monto'),
            id_usuario=id_usuario
        )
        return jsonify({"estado": "exito", "data": respuesta}), 201
    except (ValueError, PermissionError) as e:
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
    formato = request.args.get('formato', 'pdf').lower()
    try:
        datos = generar_estado_resultados()
        if formato == 'pdf':
            pdf_stream = exportar_estado_resultados_pdf(datos)
            return send_file(pdf_stream, mimetype='application/pdf', as_attachment=True, download_name='estado_resultados.pdf')
        elif formato == 'excel':
            excel_stream = exportar_estado_resultados_excel(datos)
            return send_file(excel_stream, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='estado_resultados.xlsx')
        else:
            return jsonify({"estado": "error", "mensaje": "Formato no soportado. Use 'pdf' o 'excel'."}), 400
    except ValueError as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 400
    
    
# Rutas de renderizado HTML
AVISO_SIN_DATOS = "Aún no hay movimientos registrados (ventas de inventario, nómina o gastos). Mostrando valores en cero."


@contabilidad_bp.route('/ver-estado-resultados', methods=['GET'])
@login_requerido
def ver_estado_resultados_html():
    aviso = None
    try:
        datos = generar_estado_resultados()
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {'ingresos_totales': 0.0, 'costo_ventas': 0.0, 'utilidad_bruta': 0.0,
                 'gastos_operativos': 0.0,
                 'desglose_gastos': {'nomina': 0.0, 'gastos_deducibles': 0.0, 'perdidas_inventario': 0.0},
                 'utilidad_neta': 0.0}
    return render_template('contabilidad/estado_resultados.html', data=datos, aviso=aviso)


@contabilidad_bp.route('/ver-balance-general', methods=['GET'])
@login_requerido
def ver_balance_general_html():
    aviso = None
    try:
        datos = calcular_balance_general()
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {'activos': {'efectivo_caja': 0.0, 'inventario': 0.0, 'total_activos': 0.0},
                 'pasivos': {'pasivos_laborales': 0.0, 'total_pasivos': 0.0},
                 'patrimonio': {'utilidad_ejercicio': 0.0, 'total_patrimonio': 0.0}}
    return render_template('contabilidad/balance_general.html', data=datos, aviso=aviso)


@contabilidad_bp.route('/ver-registrar-gasto', methods=['GET'])
@login_requerido
def ver_registrar_gasto_html():
    return render_template('contabilidad/registrar_gasto.html')
