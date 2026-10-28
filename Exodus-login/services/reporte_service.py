import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def exportar_estado_resultados_pdf(datos_reporte):
    """Genera un archivo PDF en memoria del Estado de Resultados."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    # Título del Reporte
    elementos.append(Paragraph("<b>ESTADO DE RESULTADOS CONSOLIDADO</b>", styles['Title']))
    elementos.append(Spacer(1, 12))

    # Tabla de Rubros Financieros
    tabla_datos = [
        ['Rubro Contable', 'Monto ($)'],
        ['Ingresos Totales', f"${datos_reporte['ingresos_totales']:,.2f}"],
        ['Costo de Ventas', f"${datos_reporte['costo_ventas']:,.2f}"],
        ['Utilidad Bruta', f"${datos_reporte['utilidad_bruta']:,.2f}"],
        ['Gastos Operativos (Nómina + Deducibles + Pérdidas)', f"${datos_reporte['gastos_operativos']:,.2f}"],
        ['UTILIDAD NETA', f"${datos_reporte['utilidad_neta']:,.2f}"]
    ]

    t = Table(tabla_datos, colWidths=[300, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))

    elementos.append(t)
    doc.build(elementos)
    buffer.seek(0)
    return buffer

def exportar_estado_resultados_excel(datos_reporte):
    """Genera una hoja de cálculo Excel en memoria del Estado de Resultados."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Estado de Resultados"

    ws.append(["Rubro Contable", "Monto ($)"])
    ws.append(["Ingresos Totales", datos_reporte['ingresos_totales']])
    ws.append(["Costo de Ventas", datos_reporte['costo_ventas']])
    ws.append(["Utilidad Bruta", datos_reporte['utilidad_bruta']])
    ws.append(["Gastos Operativos", datos_reporte['gastos_operativos']])
    ws.append(["UTILIDAD NETA", datos_reporte['utilidad_neta']])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer