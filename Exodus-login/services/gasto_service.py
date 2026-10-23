from models.contabilidad import insertar_gasto

def registrar_gasto_deducible(descripcion, monto, id_usuario):
    """
    CU-02: Valida y registra un gasto deducible.
    Muestra mensajes claros en español si los datos no son válidos.
    """
    # Validar campos vacíos
    if not descripcion or str(descripcion).strip() == "":
        raise ValueError("Error al registrar gasto: La descripción es obligatoria y no puede estar vacía.")

    # Validar que el monto sea un número válido y mayor a cero
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        raise ValueError("Error al registrar gasto: El monto debe ser un valor numérico válido.")

    if monto_float <= 0:
        raise ValueError("Error al registrar gasto: El monto debe ser mayor a cero (0).")

    # Guardar en base de datos
    id_gasto_creado = insertar_gasto(descripcion.strip(), monto_float, id_usuario)
    return {
        "mensaje": "Gasto deducible registrado correctamente.",
        "id_gasto": id_gasto_creado
    }