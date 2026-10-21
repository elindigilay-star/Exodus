<?php
/**
 * Historial de cálculos de nómina (parte de la postcondición del RF-8:
 * "se genera reporte con el salario neto calculado"). Útil para que el
 * frontend muestre lo ya calculado sin tener que volver a calcularlo.
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

try {
    $stmt = $pdo->query(
        'SELECT n.*, e.nombres, e.apellidos
         FROM nomina n
         JOIN empleados e ON e.id_empleado = n.id_empleado
         ORDER BY n.generado_en DESC
         LIMIT 50'
    );
    echo json_encode($stmt->fetchAll());
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al consultar el historial de nómina: ' . $e->getMessage()]);
}
