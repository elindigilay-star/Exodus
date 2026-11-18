import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from services.estado_resultados_service import generar_estado_resultados
from services.balance_service import calcular_balance_general
from services.consolidacion_service import consolidar_informacion_contable
from services.libro_diario_service import generar_libro_diario
from services.libro_mayor_service import generar_libro_mayor
from services.balance_comprobacion_service import generar_balance_comprobacion


# ---------------------------------------------------------------
# Helpers de formato
# ---------------------------------------------------------------
def _monto(valor):
    try:
        v = float(valor)
        if v < 0:
            return f'<font color="#B42318">${abs(v):,.2f}</font>'
        return f"${v:,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _fecha_texto(valor):
    """Convierte una fecha (datetime, date o string) a formato 'YYYY-MM-DD'."""
    if valor is None:
        return ""
    if hasattr(valor, 'strftime'):
        return valor.strftime('%Y-%m-%d')
    texto = str(valor)
    return texto[:10]


def _encabezado_reporte(titulo, subtitulo=None):
    styles = getSampleStyleSheet()
    elementos = []
    elementos.append(Paragraph(f"<b>{titulo}</b>", styles['Title']))
    if subtitulo:
        elementos.append(Paragraph(subtitulo, styles['Normal']))
        elementos.append(Spacer(1, 6))
    elementos.append(Spacer(1, 12))
    return styles, elementos


def _construir_tabla(datos_tabla, ancho_col=None, resaltar_ultima_fila=True):
    """Crea una tabla con estilo corporativo usando los colores del proyecto."""
    t = Table(datos_tabla, colWidths=ancho_col)
    estilo = [
        # Encabezado con color primario del proyecto (#1D4F91)
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D4F91')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9E0E8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if resaltar_ultima_fila:
        estilo.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F0FA')))
        estilo.append(('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'))
        estilo.append(('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1D4F91')))
    t.setStyle(TableStyle(estilo))
    return t


# ---------------------------------------------------------------
# Estado de Resultados
# ---------------------------------------------------------------
def exportar_estado_resultados_pdf(datos_reporte, periodo_txt=""):
    """Genera un archivo PDF en memoria del Estado de Resultados."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>ESTADO DE RESULTADOS CONSOLIDADO</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    tabla_datos = [
        ['Rubro Contable', 'Monto ($)'],
        ['Ingresos Totals', _monto(datos_reporte['ingresos_totales'])],
        ['Costo de Ventas', _monto(datos_reporte['costo_ventas'])],
        ['Utilidad Bruta', _monto(datos_reporte['utilidad_bruta'])],
        ['Gastos Operativos (Nómina + Deducibles + Pérdidas)',
         _monto(datos_reporte['gastos_operativos'])],
        ['UTILIDAD NETA', _monto(datos_reporte['utilidad_neta'])]
    ]
    elementos.append(_construir_tabla(tabla_datos, ancho_col=[300, 150]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_estado_resultados_excel(datos_reporte, periodo_txt=""):
    """Genera una hoja de cálculo Excel en memoria del Estado de Resultados."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Estado de Resultados"

    ws.append(["Estado de Resultados Consolidado"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    ws.append(["Rubro Contable", "Monto ($)"])
    ws.append(["Ingresos Totals", datos_reporte['ingresos_totales']])
    ws.append(["Costo de Ventas", datos_reporte['costo_ventas']])
    ws.append(["Utilidad Bruta", datos_reporte['utilidad_bruta']])
    ws.append(["Gastos Operativos", datos_reporte['gastos_operativos']])
    ws.append(["UTILIDAD NETA", datos_reporte['utilidad_neta']])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Balance General
# ---------------------------------------------------------------
def exportar_balance_general_pdf(datos_balance, periodo_txt=""):
    """Genera un archivo PDF en memoria del Balance General."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>BALANCE GENERAL</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    tabla_datos = [
        ['Estructura Financiera', 'Valor ($)'],
        ['ACTIVOS', ''],
        ['Efectivo / Flujo de Caja Disponible', _monto(datos_balance['activos']['efectivo_caja'])],
        ['Inventario de Mercancía (a costo)', _monto(datos_balance['activos']['inventario'])],
        ['Total Activos', _monto(datos_balance['activos']['total_activos'])],
        ['PASIVOS', ''],
        ['Pasivos Laborales (Retenciones)', _monto(datos_balance['pasivos']['pasivos_laborales'])],
        ['Total Pasivos', _monto(datos_balance['pasivos']['total_pasivos'])],
        ['PATRIMONIO', ''],
        ['Utilidad del Ejercicio', _monto(datos_balance['patrimonio']['utilidad_ejercicio'])],
        ['Total Patrimonio', _monto(datos_balance['patrimonio']['total_patrimonio'])]
    ]
    elementos.append(_construir_tabla(tabla_datos, ancho_col=[340, 140]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_balance_general_excel(datos_balance, periodo_txt=""):
    """Genera una hoja de cálculo Excel en memoria del Balance General."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Balance General"

    ws.append(["Balance General"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    ws.append(["Estructura Financiera", "Valor ($)"])
    ws.append(["ACTIVOS", ""])
    ws.append(["Efectivo / Flujo de Caja Disponible", datos_balance['activos']['efectivo_caja']])
    ws.append(["Inventario de Mercancía (a costo)", datos_balance['activos']['inventario']])
    ws.append(["Total Activos", datos_balance['activos']['total_activos']])
    ws.append(["PASIVOS", ""])
    ws.append(["Pasivos Laborales (Retenciones)", datos_balance['pasivos']['pasivos_laborales']])
    ws.append(["Total Pasivos", datos_balance['pasivos']['total_pasivos']])
    ws.append(["PATRIMONIO", ""])
    ws.append(["Utilidad del Ejercicio", datos_balance['patrimonio']['utilidad_ejercicio']])
    ws.append(["Total Patrimonio", datos_balance['patrimonio']['total_patrimonio']])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Consolidado
# ---------------------------------------------------------------
def exportar_consolidado_pdf(datos_consol, periodo_txt=""):
    """Genera un PDF con la información consolidada de inventario, nómina y gastos."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>CONSOLIDACIÓN DE INFORMACIÓN CONTABLE</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    tabla_datos = [
        ['Concepto', 'Valor ($)'],
        ['Ingresos Totales', _monto(datos_consol.get('ingresos_totales', 0))],
        ['Costo de Ventas', _monto(datos_consol.get('costo_ventas', 0))],
        ['Compras de Inventario', _monto(datos_consol.get('compras_inventario', 0))],
        ['Pérdidas de Inventario', _monto(datos_consol.get('perdidas_inventario', 0))],
        ['Costo de Nómina', _monto(datos_consol.get('costo_nomina', 0))],
        ['Deducciones Nómina', _monto(datos_consol.get('deducciones_nomina', 0))],
        ['Gastos Deducibles', _monto(datos_consol.get('gastos_deducibles', 0))],
        ['Valor Inventario (final)', _monto(datos_consol.get('valor_inventario', 0))],
        ['Valor Inventario (inicial)', _monto(datos_consol.get('valor_inventario_inicial', 0))]
    ]
    elementos.append(_construir_tabla(tabla_datos, ancho_col=[300, 150]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_consolidado_excel(datos_consol, periodo_txt=""):
    """Genera un Excel con la información consolidada."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidado Contable"

    ws.append(["Consolidación de Información Contable"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    ws.append(["Concepto", "Valor ($)"])
    filas = [
        ("Ingresos Totales", datos_consol.get('ingresos_totales', 0)),
        ("Costo de Ventas", datos_consol.get('costo_ventas', 0)),
        ("Compras de Inventario", datos_consol.get('compras_inventario', 0)),
        ("Pérdidas de Inventario", datos_consol.get('perdidas_inventario', 0)),
        ("Costo de Nómina", datos_consol.get('costo_nomina', 0)),
        ("Deducciones Nómina", datos_consol.get('deducciones_nomina', 0)),
        ("Gastos Deducibles", datos_consol.get('gastos_deducibles', 0)),
        ("Valor Inventario (final)", datos_consol.get('valor_inventario', 0)),
        ("Valor Inventario (inicial)", datos_consol.get('valor_inventario_inicial', 0)),
    ]
    for concepto, valor in filas:
        ws.append([concepto, valor])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Libro Diario
# ---------------------------------------------------------------
def _celda(texto, estilo='Normal'):
    """Crea una celda con texto que se ajusta al ancho de columna."""
    return Paragraph(str(texto), styles[estilo])


def exportar_libro_diario_pdf(datos_diario, periodo_txt=""):
    """Genera un archivo PDF en memoria del Libro Diario."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    estilos_celda = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>LIBRO DIARIO</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    # Estilo para celdas con texto que se ajusta
    from reportlab.lib.styles import ParagraphStyle
    estilo_texto = ParagraphStyle(
        'celda_texto', parent=estilos_celda['Normal'], fontSize=8, leading=10
    )
    estilo_texto_negrita = ParagraphStyle(
        'celda_texto_negrita', parent=estilos_celda['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold'
    )

    tabla_datos = [
        [
            Paragraph('<b>Fecha</b>', estilo_texto_negrita),
            Paragraph('<b>Asiento</b>', estilo_texto_negrita),
            Paragraph('<b>Descripción</b>', estilo_texto_negrita),
            Paragraph('<b>Cuenta</b>', estilo_texto_negrita),
            Paragraph('<b>Debe ($)</b>', estilo_texto_negrita),
            Paragraph('<b>Haber ($)</b>', estilo_texto_negrita),
        ],
    ]

    total_debe = 0.0
    total_haber = 0.0

    for asiento in datos_diario:
        fecha = _fecha_texto(asiento.get('fecha'))
        numero = asiento.get('numero_asiento', '-')
        descripcion = asiento.get('descripcion', '-')

        movimientos = asiento.get('movimientos', [])
        if movimientos:
            for i, m in enumerate(movimientos):
                debe = float(m.get('debe', 0) or 0)
                haber = float(m.get('haber', 0) or 0)
                total_debe += debe
                total_haber += haber

                fila = [
                    Paragraph(fecha if i == 0 else '', estilo_texto),
                    Paragraph(numero if i == 0 else '', estilo_texto),
                    Paragraph(descripcion if i == 0 else '', estilo_texto),
                    Paragraph(f"{m.get('codigo_cuenta', '')} - {m.get('nombre_cuenta', '')}", estilo_texto),
                    Paragraph(_monto(debe), estilo_texto),
                    Paragraph(_monto(haber), estilo_texto),
                ]
                tabla_datos.append(fila)
        else:
            tabla_datos.append([
                Paragraph(fecha, estilo_texto),
                Paragraph(numero, estilo_texto),
                Paragraph(descripcion, estilo_texto),
                Paragraph('-', estilo_texto),
                Paragraph('$0.00', estilo_texto),
                Paragraph('$0.00', estilo_texto),
            ])

    # Fila de totales generales
    tabla_datos.append([
        Paragraph('', estilo_texto),
        Paragraph('<b>TOTALES</b>', estilo_texto_negrita),
        Paragraph('', estilo_texto),
        Paragraph('', estilo_texto),
        Paragraph(f'<b>{_monto(total_debe)}</b>', estilo_texto_negrita),
        Paragraph(f'<b>{_monto(total_haber)}</b>', estilo_texto_negrita),
    ])

    elementos.append(_construir_tabla(tabla_datos, ancho_col=[65, 55, 130, 150, 75, 75], resaltar_ultima_fila=True))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_libro_diario_excel(datos_diario, periodo_txt=""):
    """Genera un archivo Excel en memoria del Libro Diario."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Libro Diario"

    ws.append(["Libro Diario"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    ws.append(["Fecha", "Asiento", "Descripción", "Cuenta", "Debe ($)", "Haber ($)"])

    for asiento in datos_diario:
        fecha = _fecha_texto(asiento.get('fecha'))
        numero = asiento.get('numero_asiento', '-')
        descripcion = asiento.get('descripcion', '-')

        movimientos = asiento.get('movimientos', [])
        if movimientos:
            for m in movimientos:
                ws.append([
                    fecha,
                    numero,
                    descripcion,
                    f"{m.get('codigo_cuenta', '')} - {m.get('nombre_cuenta', '')}",
                    float(m.get('debe', 0) or 0),
                    float(m.get('haber', 0) or 0),
                ])
        else:
            ws.append([fecha, numero, descripcion, '-', 0.0, 0.0])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Libro Mayor
# ---------------------------------------------------------------
def exportar_libro_mayor_pdf(datos_mayor, periodo_txt=""):
    """Genera un archivo PDF en memoria del Libro Mayor."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>LIBRO MAYOR</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    tabla_datos = [
        ['Código', 'Cuenta', 'Naturaleza', 'Total Debe ($)', 'Total Haber ($)', 'Saldo ($)'],
    ]

    total_debe = 0.0
    total_haber = 0.0
    total_saldo = 0.0

    for cuenta in datos_mayor:
        debe = float(cuenta.get('total_debe', 0) or 0)
        haber = float(cuenta.get('total_haber', 0) or 0)
        saldo = float(cuenta.get('saldo', 0) or 0)
        total_debe += debe
        total_haber += haber
        total_saldo += saldo

        tabla_datos.append([
            cuenta.get('codigo', '-'),
            cuenta.get('nombre', '-'),
            cuenta.get('naturaleza', '-'),
            _monto(debe),
            _monto(haber),
            _monto(saldo),
        ])

    tabla_datos.append([
        '', 'TOTALES', '',
        _monto(total_debe),
        _monto(total_haber),
        _monto(total_saldo),
    ])

    elementos.append(_construir_tabla(tabla_datos, ancho_col=[60, 180, 80, 100, 100, 100], resaltar_ultima_fila=True))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_libro_mayor_excel(datos_mayor, periodo_txt=""):
    """Genera un archivo Excel en memoria del Libro Mayor."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Libro Mayor"

    ws.append(["Libro Mayor"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    ws.append(["Código", "Cuenta", "Naturaleza", "Total Debe ($)", "Total Haber ($)", "Saldo ($)"])

    total_debe = 0.0
    total_haber = 0.0
    total_saldo = 0.0

    for cuenta in datos_mayor:
        debe = float(cuenta.get('total_debe', 0) or 0)
        haber = float(cuenta.get('total_haber', 0) or 0)
        saldo = float(cuenta.get('saldo', 0) or 0)
        total_debe += debe
        total_haber += haber
        total_saldo += saldo

        ws.append([
            cuenta.get('codigo', '-'),
            cuenta.get('nombre', '-'),
            cuenta.get('naturaleza', '-'),
            debe,
            haber,
            saldo,
        ])

    ws.append(['', 'TOTALES', '', total_debe, total_haber, total_saldo])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Balance de Comprobación
# ---------------------------------------------------------------
def exportar_balance_comprobacion_pdf(datos_balance, periodo_txt=""):
    """Genera un archivo PDF en memoria del Balance de Comprobación."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("<b>BALANCE DE COMPROBACIÓN</b>", styles['Title']))
    if periodo_txt:
        elementos.append(Paragraph(f"Periodo: {periodo_txt}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    totales = datos_balance.get('totales', {})
    cuadrado = datos_balance.get('cuadrado', False)

    estado_txt = "CUADRADO" if cuadrado else "DESCUADRADO"
    elementos.append(Paragraph(f"Estado del balance: <b>{estado_txt}</b>", styles['Normal']))
    elementos.append(Spacer(1, 6))

    tabla_datos = [
        ['Código', 'Cuenta', 'Naturaleza', 'Saldo Deudor ($)', 'Saldo Acreedor ($)'],
    ]

    for cuenta in datos_balance.get('cuentas', []):
        tabla_datos.append([
            cuenta.get('codigo', '-'),
            cuenta.get('nombre', '-'),
            cuenta.get('naturaleza', '-'),
            _monto(cuenta.get('saldo_deudor', 0)),
            _monto(cuenta.get('saldo_acreedor', 0)),
        ])

    tabla_datos.append([
        '', 'TOTALES', '',
        _monto(totales.get('total_deudor', 0)),
        _monto(totales.get('total_acreedor', 0)),
    ])

    elementos.append(_construir_tabla(tabla_datos, ancho_col=[60, 180, 80, 130, 130], resaltar_ultima_fila=True))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def exportar_balance_comprobacion_excel(datos_balance, periodo_txt=""):
    """Genera un archivo Excel en memoria del Balance de Comprobación."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Balance Comprobacion"

    ws.append(["Balance de Comprobación"])
    if periodo_txt:
        ws.append(["Periodo", periodo_txt])
    ws.append([])
    totales = datos_balance.get('totales', {})
    cuadrado = datos_balance.get('cuadrado', False)
    estado_txt = "CUADRADO" if cuadrado else "DESCUADRADO"
    ws.append(["Estado del balance", estado_txt])
    ws.append([])
    ws.append(["Código", "Cuenta", "Naturaleza", "Saldo Deudor ($)", "Saldo Acreedor ($)"])

    for cuenta in datos_balance.get('cuentas', []):
        ws.append([
            cuenta.get('codigo', '-'),
            cuenta.get('nombre', '-'),
            cuenta.get('naturaleza', '-'),
            float(cuenta.get('saldo_deudor', 0) or 0),
            float(cuenta.get('saldo_acreedor', 0) or 0),
        ])

    ws.append(['', 'TOTALES', '', float(totales.get('total_deudor', 0) or 0), float(totales.get('total_acreedor', 0) or 0)])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# Funciones de conveniencia para rutas (obtener datos + periodo)
# ---------------------------------------------------------------
def obtener_estado_resultados_con_periodo(fecha_inicio=None, fecha_fin=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    datos = generar_estado_resultados(fecha_inicio, fecha_fin)
    return datos, periodo_txt


def obtener_balance_con_periodo(fecha_inicio=None, fecha_fin=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    datos = calcular_balance_general(fecha_inicio, fecha_fin)
    return datos, periodo_txt


def obtener_consolidado_con_periodo(fecha_inicio=None, fecha_fin=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    datos = consolidar_informacion_contable(fecha_inicio, fecha_fin)
    return datos, periodo_txt


def obtener_libro_diario_con_periodo(fecha_inicio=None, fecha_fin=None, estado=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    datos = generar_libro_diario(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estado=estado)
    return datos, periodo_txt


def obtener_libro_mayor_con_periodo(fecha_inicio=None, fecha_fin=None, id_cuenta=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    id_cuenta = int(id_cuenta) if id_cuenta else None
    datos = generar_libro_mayor(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, id_cuenta=id_cuenta)
    return datos, periodo_txt


def obtener_balance_comprobacion_con_periodo(fecha_inicio=None, fecha_fin=None):
    periodo_txt = ""
    if fecha_inicio and fecha_fin:
        periodo_txt = f"{fecha_inicio} al {fecha_fin}"
    datos = generar_balance_comprobacion(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    return datos, periodo_txt
