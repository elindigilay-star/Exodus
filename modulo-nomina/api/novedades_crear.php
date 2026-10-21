<?php
/**
 * RF-9: Gestionar Ausencias, Vacaciones y Permisos
 * Secuencia normal: 1) el empleado registra solicitud -> 2) el sistema
 * valida disponibilidad -> (3-5 pasan en novedades_actualizar_estado.php,
 * cuando el administrador aprueba o rechaza)
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Método no permitido']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true) ?? $_POST;
$id_empleado  = $data['id_empleado'] ?? null;
$tipo         = $data['tipo'] ?? null; // AUSENCIA | VACACIONES | PERMISO
$fecha_inicio = $data['fecha_inicio'] ?? null;
$fecha_fin    = $data['fecha_fin'] ?? null;
$motivo       = trim($data['motivo'] ?? '');

// EXCEPCIÓN paso 2: solicitud incompleta -> se pide corrección
if (!$id_empleado || !$tipo || !$fecha_inicio || !$fecha_fin) {
    http_response_code(422);
    echo json_encode(['error' => 'Solicitud incompleta: empleado, tipo y fechas son obligatorios.']);
    exit;
}

if (!in_array($tipo, ['AUSENCIA', 'VACACIONES', 'PERMISO'], true)) {
    http_response_code(422);
    echo json_encode(['error' => 'Tipo de novedad inválido.']);
    exit;
}

if (strtotime($fecha_fin) < strtotime($fecha_inicio)) {
    http_response_code(422);
    echo json_encode(['error' => 'La fecha fin no puede ser anterior a la fecha de inicio.']);
    exit;
}

try {
    // PASO 2: "El sistema valida disponibilidad": no dejamos que el mismo
    // empleado tenga dos solicitudes activas (pendiente/aprobada) que se
    // crucen en fechas.
    $stmtCheck = $pdo->prepare(
        'SELECT id_novedad FROM novedades
         WHERE id_empleado = :id_empleado
           AND estado IN ("PENDIENTE","APROBADA")
           AND NOT (fecha_fin < :fecha_inicio OR fecha_inicio > :fecha_fin)'
    );
    $stmtCheck->execute([
        'id_empleado'   => $id_empleado,
        'fecha_inicio'  => $fecha_inicio,
        'fecha_fin'     => $fecha_fin,
    ]);

    if ($stmtCheck->fetch()) {
        // EXCEPCIÓN paso 2: no hay disponibilidad -> rechaza la solicitud
        http_response_code(409);
        echo json_encode(['error' => 'Ya existe una solicitud en ese rango de fechas para este empleado.']);
        exit;
    }

    $stmt = $pdo->prepare(
        'INSERT INTO novedades (id_empleado, tipo, fecha_inicio, fecha_fin, motivo, estado)
         VALUES (:id_empleado, :tipo, :fecha_inicio, :fecha_fin, :motivo, "PENDIENTE")'
    );
    $stmt->execute([
        'id_empleado'  => $id_empleado,
        'tipo'         => $tipo,
        'fecha_inicio' => $fecha_inicio,
        'fecha_fin'    => $fecha_fin,
        'motivo'       => $motivo,
    ]);

    echo json_encode([
        'mensaje'    => 'Solicitud registrada. Queda pendiente de aprobación.',
        'id_novedad' => $pdo->lastInsertId(),
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al registrar la solicitud: ' . $e->getMessage()]);
}
