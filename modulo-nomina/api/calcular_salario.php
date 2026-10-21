<?php
/**
 * RF-8: Calcular Salario Neto con Deducciones y Aportes
 * Secuencia normal:
 *   1) admin elige "Calcular Salario Neto" (lo dispara el front)
 *   2) el sistema solicita/recibe los datos del empleado
 *   3) aplica deducciones configuradas
 *   4) aplica aportes correspondientes
 *   5) calcula el salario neto
 *   6) genera y muestra el reporte
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
$periodo     = $data['periodo'] ?? null; // formato 'YYYY-MM'

// PASO 2 / EXCEPCIÓN: si faltan datos del empleado, se pide corrección
if (!$id_empleado || !$periodo) {
    http_response_code(422);
    echo json_encode(['error' => 'Faltan datos: selecciona un empleado y un periodo (AAAA-MM).']);
    exit;
}

try {
    $stmtEmp = $pdo->prepare('SELECT * FROM empleados WHERE id_empleado = :id AND estado = "ACTIVO"');
    $stmtEmp->execute(['id' => $id_empleado]);
    $empleado = $stmtEmp->fetch();

    if (!$empleado) {
        http_response_code(404);
        echo json_encode(['error' => 'Empleado no encontrado o inactivo.']);
        exit;
    }

    // PASO 3: aplica deducciones configuradas
    $deducciones = $pdo->query('SELECT * FROM deducciones WHERE activo = 1')->fetchAll();

    // EXCEPCIÓN paso 3: si no existe configuración de deducciones, se detiene el cálculo
    if (count($deducciones) === 0) {
        http_response_code(409);
        echo json_encode(['error' => 'No existe configuración de deducciones. Cálculo detenido.']);
        exit;
    }

    // PASO 4: aplica aportes correspondientes
    $aportes = $pdo->query('SELECT * FROM aportes WHERE activo = 1')->fetchAll();

    $salario_base = (float) $empleado['salario_base'];

    $total_deducciones = 0.0;
    foreach ($deducciones as $d) {
        $total_deducciones += $salario_base * ((float) $d['porcentaje'] / 100);
    }

    $total_aportes = 0.0;
    foreach ($aportes as $a) {
        $total_aportes += $salario_base * ((float) $a['porcentaje'] / 100);
    }

    // PASO 5: los aportes los paga el empleador, no se le restan al empleado;
    // solo se muestran en el reporte como costo de nómina de la empresa.
    $salario_neto = $salario_base - $total_deducciones;

    // PASO 6: genera y guarda el reporte
    $stmtInsert = $pdo->prepare(
        'INSERT INTO nomina (id_empleado, periodo, salario_base, total_deducciones, total_aportes, salario_neto)
         VALUES (:id_empleado, :periodo, :salario_base, :total_deducciones, :total_aportes, :salario_neto)'
    );
    $stmtInsert->execute([
        'id_empleado'        => $id_empleado,
        'periodo'            => $periodo,
        'salario_base'       => $salario_base,
        'total_deducciones'  => $total_deducciones,
        'total_aportes'      => $total_aportes,
        'salario_neto'       => $salario_neto,
    ]);

    echo json_encode([
        'mensaje' => 'Nómina calculada correctamente.',
        'reporte' => [
            'empleado'               => $empleado['nombres'] . ' ' . $empleado['apellidos'],
            'periodo'                => $periodo,
            'salario_base'           => round($salario_base, 2),
            'total_deducciones'      => round($total_deducciones, 2),
            'total_aportes_empleador'=> round($total_aportes, 2),
            'salario_neto'           => round($salario_neto, 2),
        ],
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al calcular el salario: ' . $e->getMessage()]);
}
