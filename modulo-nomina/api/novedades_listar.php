<?php
/**
 * Lista solicitudes de ausencias/vacaciones/permisos, con el nombre del
 * empleado ya incluido (JOIN) para no hacer una consulta por fila en el
 * frontend. ?estado=PENDIENTE filtra; sin parámetro trae todas.
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

$estado = $_GET['estado'] ?? null;

try {
    $sql = 'SELECT n.*, e.nombres, e.apellidos
            FROM novedades n
            JOIN empleados e ON e.id_empleado = n.id_empleado';

    if ($estado) {
        $sql .= ' WHERE n.estado = :estado';
    }
    $sql .= ' ORDER BY n.creado_en DESC';

    $stmt = $pdo->prepare($sql);
    $stmt->execute($estado ? ['estado' => $estado] : []);

    echo json_encode($stmt->fetchAll());
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al consultar novedades: ' . $e->getMessage()]);
}
