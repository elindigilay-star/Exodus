<?php
/**
 * RF-7: Eliminar Empleados
 * Secuencia normal: 1) admin elige "Eliminar" -> 2) llega el id ->
 * 3) el sistema valida que exista -> 4) (confirmación ya la hizo el front) ->
 * 5) elimina -> 6) actualiza BD y responde éxito.
 *
 * Decisión de diseño: en vez de DELETE físico, se hace un "borrado lógico"
 * (estado = INACTIVO). Motivos:
 *   - La tabla nomina y novedades tienen llave foránea hacia empleados:
 *     un DELETE real fallaría o rompería el historial de nómina.
 *   - La postcondición del RF-7 pide que el empleado "no pueda acceder a
 *     la aplicación", no que su historial desaparezca (buena práctica
 *     contable: nunca se borra el rastro de pagos ya hechos).
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Método no permitido']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true) ?? $_POST;
$id_empleado = $data['id_empleado'] ?? null;

if (!$id_empleado) {
    http_response_code(422);
    echo json_encode(['error' => 'Falta el identificador del empleado.']);
    exit;
}

try {
    // PASO 3: el sistema valida que el empleado exista
    $check = $pdo->prepare('SELECT id_empleado FROM empleados WHERE id_empleado = :id');
    $check->execute(['id' => $id_empleado]);
    if (!$check->fetch()) {
        // EXCEPCIÓN paso 3
        http_response_code(404);
        echo json_encode(['error' => 'El empleado no existe.']);
        exit;
    }

    // PASO 5 y 6
    $stmt = $pdo->prepare('UPDATE empleados SET estado = "INACTIVO" WHERE id_empleado = :id');
    $stmt->execute(['id' => $id_empleado]);

    echo json_encode(['mensaje' => 'Empleado eliminado correctamente.']);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al eliminar el empleado: ' . $e->getMessage()]);
}
