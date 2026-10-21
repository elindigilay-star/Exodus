<?php
/**
 * RF-6: Registrar Empleados
 * Secuencia normal: 1) admin envía datos -> 2) (ya llegan) ->
 * 3) el sistema valida -> 4) si es correcta, guarda -> 5) asigna estado ACTIVO
 */
require_once __DIR__ . '/../config/db.php';
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Método no permitido']);
    exit;
}

// Acepta tanto JSON (fetch con body JSON) como form-data normal
$data = json_decode(file_get_contents('php://input'), true) ?? $_POST;

$nombres       = trim($data['nombres'] ?? '');
$apellidos     = trim($data['apellidos'] ?? '');
$documento     = trim($data['documento'] ?? '');
$cargo         = trim($data['cargo'] ?? '');
$salario_base  = $data['salario_base'] ?? null;
$fecha_ingreso = $data['fecha_ingreso'] ?? null;

// PASO 3: "El sistema valida la información"
// EXCEPCIÓN paso 5: si los datos son incompletos, se pide corrección
if ($nombres === '' || $apellidos === '' || $documento === '' || !$salario_base || !$fecha_ingreso) {
    http_response_code(422);
    echo json_encode(['error' => 'Datos incompletos: nombres, apellidos, documento, salario base y fecha de ingreso son obligatorios.']);
    exit;
}

if (!is_numeric($salario_base) || (float) $salario_base <= 0) {
    http_response_code(422);
    echo json_encode(['error' => 'El salario base debe ser un número mayor a 0.']);
    exit;
}

try {
    // EXCEPCIÓN paso 5: si el empleado ya existe, se detiene el registro
    $check = $pdo->prepare('SELECT id_empleado FROM empleados WHERE documento = :documento');
    $check->execute(['documento' => $documento]);
    if ($check->fetch()) {
        http_response_code(409);
        echo json_encode(['error' => 'Ya existe un empleado registrado con ese número de documento.']);
        exit;
    }

    // PASO 4 y 5: guarda el registro y lo marca ACTIVO
    $stmt = $pdo->prepare(
        'INSERT INTO empleados (nombres, apellidos, documento, cargo, salario_base, fecha_ingreso, estado)
         VALUES (:nombres, :apellidos, :documento, :cargo, :salario_base, :fecha_ingreso, "ACTIVO")'
    );
    $stmt->execute([
        'nombres'       => $nombres,
        'apellidos'     => $apellidos,
        'documento'     => $documento,
        'cargo'         => $cargo,
        'salario_base'  => $salario_base,
        'fecha_ingreso' => $fecha_ingreso,
    ]);

    echo json_encode([
        'mensaje'     => 'Empleado registrado correctamente.',
        'id_empleado' => $pdo->lastInsertId(),
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error al registrar el empleado: ' . $e->getMessage()]);
}
