from models.contabilidad import (
    insertar_gasto, obtener_total_gastos, listar_gastos, obtener_gasto,
    actualizar_gasto, anular_gasto
)


def registrar_gasto_deducible(descripcion, monto, id_usuario, categoria=None,
                              tercero=None, nit=None, numero_documento=None, fecha=None):
    """
    CU-02: Valida y registra un gasto deducible.
    Muestra mensajes claros en español si los datos no son válidos.
    """
    # Validar descripción obligatoria
    if not descripcion or str(descripcion).strip() == "":
        raise ValueError("Error al registrar gasto: La descripción es obligatoria y no puede estar vacía.")

    # Validar monto numérico y mayor a cero
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        raise ValueError("Error al registrar gasto: El monto debe ser un valor numérico válido.")

    if monto_float <= 0:
        raise ValueError("Error al registrar gasto: El monto debe ser mayor a cero (0).")

    # Validar fecha si se envía
    if fecha is not None and str(fecha).strip() != "":
        try:
            from datetime import datetime
            datetime.strptime(str(fecha), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Error al registrar gasto: La fecha tiene un formato inválido (use AAAA-MM-DD).")

    # Guardar en base de datos
    id_gasto_creado = insertar_gasto(
        descripcion.strip(), monto_float, id_usuario,
        categoria=categoria, tercero=tercero, nit=nit,
        numero_documento=numero_documento, fecha=fecha
    )
    return {
        "mensaje": "Gasto deducible registrado correctamente.",
        "id_gasto": id_gasto_creado
    }


def editar_gasto_deducible(id_gasto, descripcion, monto, categoria=None,
                           tercero=None, nit=None, numero_documento=None, fecha=None):
    """CU-02b: Valida y actualiza un gasto deducible existente."""
    if not descripcion or str(descripcion).strip() == "":
        raise ValueError("Error al editar gasto: La descripción es obligatoria y no puede estar vacía.")

    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        raise ValueError("Error al editar gasto: El monto debe ser un valor numérico válido.")

    if monto_float <= 0:
        raise ValueError("Error al editar gasto: El monto debe ser mayor a cero (0).")

    if fecha is not None and str(fecha).strip() != "":
        try:
            from datetime import datetime
            datetime.strptime(str(fecha), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Error al editar gasto: La fecha tiene un formato inválido (use AAAA-MM-DD).")

    filas_afectadas = actualizar_gasto(
        id_gasto, descripcion.strip(), monto_float,
        categoria=categoria, tercero=tercero, nit=nit,
        numero_documento=numero_documento, fecha=fecha
    )
    if filas_afectadas == 0:
        raise ValueError("Error al editar gasto: El gasto no existe o ya fue anulado.")

    return {"mensaje": "Gasto deducible actualizado correctamente.", "id_gasto": id_gasto}


def anular_gasto_deducible(id_gasto):
    """CU-02c: Anula lógicamente un gasto deducible."""
    filas_afectadas = anular_gasto(id_gasto)
    if filas_afectadas == 0:
        raise ValueError("Error al anular gasto: El gasto no existe o ya fue anulado.")
    return {"mensaje": "Gasto deducible anulado correctamente.", "id_gasto": id_gasto}


def obtener_gasto_deducible(id_gasto):
    """Obtiene los datos de un gasto deducible para edición."""
    return obtener_gasto(id_gasto)


def listar_gastos_deducibles(fecha_inicio=None, fecha_fin=None, estado_gasto='ACTIVO'):
    """Lista gastos deducibles con metadatos completos."""
    return listar_gastos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estado_gasto=estado_gasto)
