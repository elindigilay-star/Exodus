<?php
/**
 * Lista empleados. No corresponde a un solo RF: lo usan RF-7, RF-8 y RF-9
 * para llenar los combos de "elige un empleado" del frontend.
 * ?estado=ACTIVO o ?estado=INACTIVO filtra; sin parámetro trae todos.
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

$estado = $_GET['estado'] ?? null;

try {
    if ($estado) {
        $stmt = $pdo->prepare('SELECT * FROM empleados WHERE estado = :estado ORDER BY id_empleado DESC');
        $stmt->execute(['estado' => $estado]);
    } else {
        $stmt = $pdo->query('SELECT * FROM empleados ORDER BY id_empleado DESC');
    }
    echo json_encode($stmt->fetchAll());
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al consultar empleados: ' . $e->getMessage()]);
}
