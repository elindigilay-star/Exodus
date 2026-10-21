import pymysql
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from db import get_db
from seguridad import rol_requerido

bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")
ROLES = ("administrador", "contador")
TIPOS = ("producto", "impuesto")


def _leer_formulario():
    nombre = request.form.get("nombre", "").strip()
    tipo = request.form.get("tipo", "")
    try:
        porcentaje = float(request.form.get("porcentaje", "0").replace(",", "."))
    except ValueError:
        return None, "El porcentaje debe ser un número."
    if not nombre:
        return None, "Escribe el nombre de la etiqueta."
    if tipo not in TIPOS:
        return None, "Elige un tipo válido."
    if not 0 <= porcentaje <= 100:
        return None, "El porcentaje debe estar entre 0 y 100."
    return (nombre, tipo, porcentaje), None


def _listar():
    return get_db().execute("SELECT * FROM etiquetas ORDER BY tipo, nombre").fetchall()


@bp.route("/etiquetas", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def etiquetas():
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db = get_db()
                db.execute("INSERT INTO etiquetas (nombre, tipo, porcentaje) VALUES (%s,%s,%s)", datos)
                db.commit()
                flash("Etiqueta creada.", "ok")
                return redirect(url_for("configuracion.etiquetas"))
            except pymysql.err.IntegrityError:
                flash("Ya existe una etiqueta con ese nombre.", "error")
    return render_template("configuracion/etiquetas.html", etiquetas=_listar(), editar=None)


@bp.route("/etiquetas/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def etiquetas_editar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM etiquetas WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db.execute("UPDATE etiquetas SET nombre=%s, tipo=%s, porcentaje=%s WHERE id=%s", (*datos, id))
                db.commit()
                flash("Etiqueta actualizada.", "ok")
                return redirect(url_for("configuracion.etiquetas"))
            except pymysql.err.IntegrityError:
                flash("Ya existe una etiqueta con ese nombre.", "error")
    return render_template("configuracion/etiquetas.html", etiquetas=_listar(), editar=fila)


@bp.route("/etiquetas/<int:id>/eliminar", methods=["POST"])
@rol_requerido(*ROLES)
def etiquetas_eliminar(id):
    db = get_db()
    db.execute("DELETE FROM etiquetas WHERE id = %s", (id,))
    db.commit()
    flash("Etiqueta eliminada.", "ok")
    return redirect(url_for("configuracion.etiquetas"))