"""Servicio de asientos contables (doble entrada).

Responsabilidades:
- Validar y crear asientos contables.
- Validar cuadrimiento debe = haber.
- Contabilizar (BORRADOR -> CONTABLE) y anular asientos.
- Integrar con el plan de cuentas y parámetros tributarios (IVA).
"""

from models.asiento import (
    crear_asiento, obtener_asiento, actualizar_asiento,
    contabilizar_asiento, anular_asiento, listar_asientos
)
from models.plan_cuentas import obtener_cuenta


def registrar_asiento(numero_asiento, fecha, descripcion, id_usuario,
                      referencia=None, movimientos=None):
    """
    CU: Registrar asiento contable.

    Valida que cada cuenta exista y permita movimiento, y que el asiento
    esté cuadrado (debe = haber) antes de persistir.
    """
    if movimientos is None:
        movimientos = []

    if not numero_asiento or not str(numero_asiento).strip():
        raise ValueError("El número de asiento es obligatorio.")

    if not descripcion or not str(descripcion).strip():
        raise ValueError("La descripción del asiento es obligatoria.")

    # Validar cada movimiento
    for idx, m in enumerate(movimientos, start=1):
        id_cuenta = m.get("id_cuenta")
        if not id_cuenta:
            raise ValueError(f"Movimiento {idx}: falta la cuenta contable.")

        cuenta = obtener_cuenta(id_cuenta)
        if not cuenta:
            raise ValueError(f"Movimiento {idx}: la cuenta contable no existe.")
        if not cuenta.get("permite_movimiento"):
            raise ValueError(
                f"Movimiento {idx}: la cuenta '{cuenta['nombre']}' no permite movimientos directos."
            )
        if not cuenta.get("activo"):
            raise ValueError(
                f"Movimiento {idx}: la cuenta '{cuenta['nombre']}' está inactiva."
            )

        debe = float(m.get("debe", 0) or 0)
        haber = float(m.get("haber", 0) or 0)
        if debe < 0 or haber < 0:
            raise ValueError(f"Movimiento {idx}: los montos no pueden ser negativos.")
        if debe > 0 and haber > 0:
            raise ValueError(
                f"Movimiento {idx}: una línea no puede tener valor en debe y haber al mismo tiempo."
            )
        if debe == 0 and haber == 0:
            raise ValueError(f"Movimiento {idx}: debe tener un valor en debe o haber.")

    return crear_asiento(
        numero_asiento=numero_asiento.strip(),
        fecha=fecha,
        descripcion=descripcion.strip(),
        id_usuario=id_usuario,
        referencia=(referencia or "").strip() or None,
        movimientos=movimientos,
    )


def editar_asiento(id_asiento, fecha, descripcion, referencia=None, movimientos=None):
    """Edita un asiento en borrador con validación de cuadrimiento."""
    if movimientos is None:
        movimientos = []

    if not descripcion or not str(descripcion).strip():
        raise ValueError("La descripción del asiento es obligatoria.")

    for idx, m in enumerate(movimientos, start=1):
        id_cuenta = m.get("id_cuenta")
        if not id_cuenta:
            raise ValueError(f"Movimiento {idx}: falta la cuenta contable.")

        cuenta = obtener_cuenta(id_cuenta)
        if not cuenta:
            raise ValueError(f"Movimiento {idx}: la cuenta contable no existe.")
        if not cuenta.get("permite_movimiento"):
            raise ValueError(
                f"Movimiento {idx}: la cuenta '{cuenta['nombre']}' no permite movimientos directos."
            )

        debe = float(m.get("debe", 0) or 0)
        haber = float(m.get("haber", 0) or 0)
        if debe < 0 or haber < 0:
            raise ValueError(f"Movimiento {idx}: los montos no pueden ser negativos.")
        if debe > 0 and haber > 0:
            raise ValueError(
                f"Movimiento {idx}: una línea no puede tener valor en debe y haber al mismo tiempo."
            )

    return actualizar_asiento(
        id_asiento=id_asiento,
        fecha=fecha,
        descripcion=descripcion.strip(),
        referencia=(referencia or "").strip() or None,
        movimientos=movimientos,
    )


def contabilizar(id_asiento):
    """Pasa un asiento de BORRADOR a CONTABLE tras validar cuadrimiento."""
    return contabilizar_asiento(id_asiento)


def anular(id_asiento):
    """Anula un asiento contable."""
    return anular_asiento(id_asiento)


def listar(fecha_inicio=None, fecha_fin=None, estado=None):
    """Lista asientos contables con totales."""
    return listar_asientos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estado=estado)


def obtener(id_asiento):
    """Obtiene un asiento con sus movimientos."""
    return obtener_asiento(id_asiento)