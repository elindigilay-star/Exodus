<?php
/**
 * RF-9, continuación: 3) el administrador aprueba o rechaza ->
 * 4) el sistema actualiza el estado -> 5) el sistema notifica el resultado.
 *
 * EXCEPCIÓN paso 3 del RF ("si el administrador no responde, la solicitud
 * queda pendiente") ya está cubierta de forma natural: mientras este
 * endpoint no se llame, la fila se queda en estado PENDIENTE.
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Método no permitido']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true) ?? $_POST;
$id_novedad   = $data['id_novedad'] ?? null;
$nuevo_estado = $data['estado'] ?? null; // APROBADA | RECHAZADA

if (!$id_novedad || !in_array($nuevo_estado, ['APROBADA', 'RECHAZADA'], true)) {
    http_response_code(422);
    echo json_encode(['error' => 'Datos inválidos: se espera id_novedad y estado (APROBADA o RECHAZADA).']);
    exit;
}

try {
    // PASO 4
    $stmt = $pdo->prepare('UPDATE novedades SET estado = :estado WHERE id_novedad = :id');
    $stmt->execute(['estado' => $nuevo_estado, 'id' => $id_novedad]);

    if ($stmt->rowCount() === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'No se encontró la solicitud.']);
        exit;
    }

    // PASO 5: "El sistema notifica resultado". Aquí se simula devolviendo el
    // mensaje al frontend; en un sistema real este sería el punto donde se
    // dispara un correo o una notificación interna.
    echo json_encode(['mensaje' => "Solicitud actualizada a {$nuevo_estado}."]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al actualizar la solicitud: ' . $e->getMessage()]);
}
