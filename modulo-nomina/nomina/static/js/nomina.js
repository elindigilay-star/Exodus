/**
 * nomina.js - Módulo de Nómina dentro de Exodus Contable (Flask).
 * Corre en el navegador y solo consume los endpoints JSON bajo /api/nomina.
 */

const API = '/api/nomina';

function formatoMoneda(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(valor);
}

function mostrarMensaje(id, texto, tipo) {
  const el = document.getElementById(id);
  el.textContent = texto;
  el.className = `msg show ${tipo}`;
  setTimeout(() => el.classList.remove('show'), 4000);
}

async function llamarApi(endpoint, opciones = {}) {
  const respuesta = await fetch(`${API}/${endpoint}`, opciones);
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.error || 'Ocurrió un error inesperado.');
  }
  return datos;
}

function post(endpoint, cuerpo) {
  return llamarApi(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  });
}

// ---------------------------------------------------------------
// Navegación entre vistas
// ---------------------------------------------------------------
document.querySelectorAll('.nomina .tab').forEach((boton) => {
  boton.addEventListener('click', () => {
    document.querySelectorAll('.nomina .tab').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.nomina .view').forEach((v) => v.classList.remove('active'));

    boton.classList.add('active');
    document.getElementById(`view-${boton.dataset.view}`).classList.add('active');
  });
});

// ---------------------------------------------------------------
// RF-6 / RF-7: Empleados
// ---------------------------------------------------------------
async function cargarEmpleados() {
  const tabla = document.getElementById('tabla-empleados');
  try {
    const empleados = await llamarApi('empleados');

    if (empleados.length === 0) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="7">Aún no hay empleados registrados.</td></tr>';
    } else {
      tabla.innerHTML = empleados.map((emp) => `
        <tr>
          <td>${emp.nombres} ${emp.apellidos}</td>
          <td>${emp.documento}</td>
          <td>${emp.cargo || '—'}</td>
          <td class="num">${formatoMoneda(emp.salario_base)}</td>
          <td>${emp.fecha_ingreso}</td>
          <td><span class="badge ${emp.estado.toLowerCase()}">${emp.estado}</span></td>
          <td>${emp.estado === 'ACTIVO'
            ? `<button class="link-danger" data-eliminar="${emp.id_empleado}">Eliminar</button>`
            : ''}</td>
        </tr>
      `).join('');
    }

    llenarSelectEmpleados(empleados.filter((e) => e.estado === 'ACTIVO'));
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="7">${err.message}</td></tr>`;
  }
}

function llenarSelectEmpleados(activos) {
  const opciones = activos
    .map((e) => `<option value="${e.id_empleado}">${e.nombres} ${e.apellidos} — ${e.documento}</option>`)
    .join('');

  document.getElementById('nom-empleado').innerHTML = opciones || '<option value="">No hay empleados activos</option>';
  document.getElementById('nov-empleado').innerHTML = opciones || '<option value="">No hay empleados activos</option>';
}

document.getElementById('form-empleado').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = await post('empleados', datos);
    mostrarMensaje('msg-empleado', resultado.mensaje, 'ok');
    form.reset();
    cargarEmpleados();
  } catch (err) {
    mostrarMensaje('msg-empleado', err.message, 'error');
  }
});

document.getElementById('tabla-empleados').addEventListener('click', async (evento) => {
  const id = evento.target.dataset.eliminar;
  if (!id) return;

  if (!confirm('¿Eliminar este empleado? Quedará marcado como inactivo.')) return;

  try {
    await post('empleados/eliminar', { id_empleado: id });
    cargarEmpleados();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// RF-8: Calcular nómina
// ---------------------------------------------------------------
async function cargarHistorialNomina() {
  const tabla = document.getElementById('tabla-nomina');
  try {
    const registros = await llamarApi('historial');

    tabla.innerHTML = registros.length === 0
      ? '<tr class="empty-row"><td colspan="5">Aún no se ha calculado ninguna nómina.</td></tr>'
      : registros.map((r) => `
        <tr>
          <td>${r.nombres} ${r.apellidos}</td>
          <td>${r.periodo}</td>
          <td class="num">${formatoMoneda(r.total_deducciones)}</td>
          <td class="num">${formatoMoneda(r.total_aportes)}</td>
          <td class="num">${formatoMoneda(r.salario_neto)}</td>
        </tr>
      `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="5">${err.message}</td></tr>`;
  }
}

document.getElementById('form-nomina').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = await post('calcular', datos);
    mostrarMensaje('msg-nomina', resultado.mensaje, 'ok');

    const rep = resultado.reporte;
    document.getElementById('rep-empleado').textContent = rep.empleado;
    document.getElementById('rep-periodo').textContent = rep.periodo;
    document.getElementById('rep-base').textContent = formatoMoneda(rep.salario_base);
    document.getElementById('rep-deducciones').textContent = formatoMoneda(rep.total_deducciones);
    document.getElementById('rep-aportes').textContent = formatoMoneda(rep.total_aportes_empleador);
    document.getElementById('rep-neto').textContent = formatoMoneda(rep.salario_neto);
    document.getElementById('reporte-nomina').classList.add('show');

    cargarHistorialNomina();
  } catch (err) {
    mostrarMensaje('msg-nomina', err.message, 'error');
  }
});

// ---------------------------------------------------------------
// RF-9: Ausencias, vacaciones y permisos
// ---------------------------------------------------------------
async function cargarNovedades() {
  const tabla = document.getElementById('tabla-novedades');
  try {
    const novedades = await llamarApi('novedades');

    tabla.innerHTML = novedades.length === 0
      ? '<tr class="empty-row"><td colspan="6">Aún no hay solicitudes registradas.</td></tr>'
      : novedades.map((n) => `
        <tr>
          <td>${n.nombres} ${n.apellidos}</td>
          <td>${n.tipo}</td>
          <td>${n.fecha_inicio}</td>
          <td>${n.fecha_fin}</td>
          <td><span class="badge ${n.estado.toLowerCase()}">${n.estado}</span></td>
          <td>${n.estado === 'PENDIENTE' ? `
            <button class="link-approve" data-aprobar="${n.id_novedad}">Aprobar</button>
            <button class="link-danger" data-rechazar="${n.id_novedad}">Rechazar</button>
          ` : ''}</td>
        </tr>
      `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="6">${err.message}</td></tr>`;
  }
}

document.getElementById('form-novedad').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = await post('novedades', datos);
    mostrarMensaje('msg-novedad', resultado.mensaje, 'ok');
    form.reset();
    cargarNovedades();
  } catch (err) {
    mostrarMensaje('msg-novedad', err.message, 'error');
  }
});

document.getElementById('tabla-novedades').addEventListener('click', async (evento) => {
  const idAprobar = evento.target.dataset.aprobar;
  const idRechazar = evento.target.dataset.rechazar;
  if (!idAprobar && !idRechazar) return;

  const id_novedad = idAprobar || idRechazar;
  const estado = idAprobar ? 'APROBADA' : 'RECHAZADA';

  try {
    await post('novedades/estado', { id_novedad, estado });
    cargarNovedades();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// Carga inicial
// ---------------------------------------------------------------
cargarEmpleados();
cargarHistorialNomina();
cargarNovedades();
