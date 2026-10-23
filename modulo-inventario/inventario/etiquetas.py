"""Rutas de Etiquetas del módulo de inventario.

Vive en `modulo-inventario/inventario/etiquetas.py` y se registra
en la app principal junto con el resto del módulo de inventario.

- Endpoints: /api/inventario/etiquetas...
- Plantilla: templates/inventario/etiquetas.html
- Modelo: inventario.modelo
"""

import pymysql
from flask import abort, flash, redirect, render_template, request, url_for

from routes.auth import requerir_roles
from . import modelo
from .rutas import inventario_modulo_bp

ROLES = ('Administrador', 'Contador')
TIPOS = ('producto', 'impuesto')


def _leer_formulario():
    nombre = request.form.get('nombre', '').strip()
    tipo = request.form.get('tipo', '')
    try:
        porcentaje = float(request.form.get('porcentaje', '0').replace(',', '.'))
    except ValueError:
        return None, 'El porcentaje debe ser un número.'
    if not nombre:
        return None, 'Escribe el nombre de la etiqueta.'
    if tipo not in TIPOS:
        return None, 'Elige un tipo válido.'
    if not 0 <= porcentaje <= 100:
        return None, 'El porcentaje debe estar entre 0 y 100.'
    return (nombre, tipo, porcentaje), None


@inventario_modulo_bp.route('/etiquetas', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def etiquetas():
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.crear_etiqueta(*datos)
                flash('Etiqueta creada.', 'ok')
                return redirect(url_for('inventario_modulo.etiquetas'))
            except pymysql.err.IntegrityError:
                flash('Ya existe una etiqueta con ese nombre.', 'error')
    return render_template(
        'inventario/etiquetas.html',
        etiquetas=modelo.listar_etiquetas(),
        editar=None,
    )


@inventario_modulo_bp.route('/etiquetas/<int:id>/editar', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def etiquetas_editar(id):
    fila = modelo.obtener_etiqueta(id)
    if fila is None:
        abort(404)
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.actualizar_etiqueta(id, *datos)
                flash('Etiqueta actualizada.', 'ok')
                return redirect(url_for('inventario_modulo.etiquetas'))
            except pymysql.err.IntegrityError:
                flash('Ya existe una etiqueta con ese nombre.', 'error')
    return render_template(
        'inventario/etiquetas.html',
        etiquetas=modelo.listar_etiquetas(),
        editar=fila,
    )


@inventario_modulo_bp.route('/etiquetas/<int:id>/eliminar', methods=['POST'])
@requerir_roles(*ROLES)
def etiquetas_eliminar(id):
    modelo.eliminar_etiqueta(id)
    flash('Etiqueta eliminada.', 'ok')
    return redirect(url_for('inventario_modulo.etiquetas'))