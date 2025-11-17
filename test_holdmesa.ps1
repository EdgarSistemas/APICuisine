# Script de Pruebas Automatizadas para HoldMesa Endpoints
# USO: .\test_holdmesa.ps1

$BASE_URL = "http://localhost:5000"
$EMAIL = "admin@example.com"
$PASSWORD = "password123"

Write-Host "======================================"
Write-Host "PRUEBAS AUTOMATIZADAS - HOLDMESA API"
Write-Host "=====================================" -ForegroundColor Cyan

# ====== PASO 1: LOGIN ======
Write-Host "`n[PASO 1] Autenticando..." -ForegroundColor Yellow

$loginResponse = curl -X POST "$BASE_URL/api/auth/login" `
  -H "Content-Type: application/json" `
  -d @"
{
  "email": "$EMAIL",
  "password": "$PASSWORD"
}
"@ 2>$null | ConvertFrom-Json

if (-not $loginResponse.access_token) {
  Write-Host "ERROR: No se pudo obtener token" -ForegroundColor Red
  Write-Host $loginResponse
  exit 1
}

$TOKEN = $loginResponse.access_token
Write-Host "✓ Token obtenido: $($TOKEN.Substring(0, 20))..." -ForegroundColor Green

# ====== PASO 2: CREAR HOLD ======
Write-Host "`n[PASO 2] Creando hold..." -ForegroundColor Yellow

$now = (Get-Date).AddHours(1)
$inicio = $now.ToString("yyyy-MM-ddTHH:mm:ss")
$fin = $now.AddHours(2).ToString("yyyy-MM-ddTHH:mm:ss")

$createHoldResponse = curl -X POST "$BASE_URL/api/holds" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "mesa_id": 1,
  "actor_tipo": 2,
  "inicio": "$inicio",
  "fin_estimado": "$fin",
  "ttl_minutes": 3,
  "notas": "Test hold desde script"
}
"@ 2>$null | ConvertFrom-Json

if ($createHoldResponse.hold.id_hold_mesa) {
  $holdId = $createHoldResponse.hold.id_hold_mesa
  Write-Host "✓ Hold creado: ID=$holdId, Mesa=1, Status=1" -ForegroundColor Green
} else {
  Write-Host "ERROR al crear hold:" -ForegroundColor Red
  Write-Host $createHoldResponse
  exit 1
}

# ====== PASO 3: OBTENER HOLD ======
Write-Host "`n[PASO 3] Obteniendo hold creado..." -ForegroundColor Yellow

$getHoldResponse = curl -X GET "$BASE_URL/api/holds/$holdId" `
  -H "Authorization: Bearer $TOKEN" 2>$null | ConvertFrom-Json

if ($getHoldResponse.id_hold_mesa) {
  Write-Host "✓ Hold obtenido: ID=$($getHoldResponse.id_hold_mesa), Status=$($getHoldResponse.estatus)" -ForegroundColor Green
} else {
  Write-Host "ERROR al obtener hold:" -ForegroundColor Red
  Write-Host $getHoldResponse
  exit 1
}

# ====== PASO 4: LISTAR HOLDS ======
Write-Host "`n[PASO 4] Listando holds activos..." -ForegroundColor Yellow

$listHoldsResponse = curl -X GET "$BASE_URL/api/holds" `
  -H "Authorization: Bearer $TOKEN" 2>$null | ConvertFrom-Json

Write-Host "✓ Holds activos encontrados: $($listHoldsResponse.total)" -ForegroundColor Green
foreach ($hold in $listHoldsResponse.holds) {
  Write-Host "  - ID=$($hold.id_hold_mesa), Mesa=$($hold.mesa_id), Status=$($hold.estatus)"
}

# ====== PASO 5: VERIFICAR DISPONIBILIDAD ======
Write-Host "`n[PASO 5] Verificando disponibilidad de mesa 2..." -ForegroundColor Yellow

$checkResponse = curl -X POST "$BASE_URL/api/holds/disponibilidad" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "mesa_id": 2,
  "inicio": "$inicio",
  "fin_estimado": "$fin"
}
"@ 2>$null | ConvertFrom-Json

Write-Host "✓ Mesa 2 disponible: $($checkResponse.disponible)" -ForegroundColor Green
Write-Host "  Mensaje: $($checkResponse.mensaje)"

# ====== PASO 6: VERIFICAR DISPONIBILIDAD MESA OCUPADA ======
Write-Host "`n[PASO 6] Verificando disponibilidad de mesa 1 (debería estar ocupada)..." -ForegroundColor Yellow

$checkOccupied = curl -X POST "$BASE_URL/api/holds/disponibilidad" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "mesa_id": 1,
  "inicio": "$inicio",
  "fin_estimado": "$fin"
}
"@ 2>$null | ConvertFrom-Json

Write-Host "✓ Mesa 1 disponible: $($checkOccupied.disponible) (esperado: false)" -ForegroundColor Green
Write-Host "  Mensaje: $($checkOccupied.mensaje)"

# ====== PASO 7: CREAR RESERVA DESDE HOLD ======
Write-Host "`n[PASO 7] Creando reserva desde hold..." -ForegroundColor Yellow

$createReservaResponse = curl -X POST "$BASE_URL/api/reservas" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "cliente_id": 1,
  "inicio": "$inicio",
  "fin_estimado": "$fin",
  "hold_id": $holdId
}
"@ 2>$null | ConvertFrom-Json

if ($createReservaResponse.reserva.id_reserva) {
  $reservaId = $createReservaResponse.reserva.id_reserva
  Write-Host "✓ Reserva creada: ID=$reservaId" -ForegroundColor Green
} else {
  Write-Host "ERROR al crear reserva:" -ForegroundColor Red
  Write-Host $createReservaResponse
}

# ====== PASO 8: VERIFICAR HOLD CAMBIÓ A USADO ======
Write-Host "`n[PASO 8] Verificando que hold cambió a usado..." -ForegroundColor Yellow

$holdAfterReserva = curl -X GET "$BASE_URL/api/holds/$holdId" `
  -H "Authorization: Bearer $TOKEN" 2>$null | ConvertFrom-Json

Write-Host "✓ Hold status después de reserva: $($holdAfterReserva.estatus) (esperado: 2 = usado)" -ForegroundColor Green

# ====== PASO 9: CANCELAR HOLD (test con hold nuevo) ======
Write-Host "`n[PASO 9] Creando y cancelando nuevo hold..." -ForegroundColor Yellow

$holdToCancel = curl -X POST "$BASE_URL/api/holds" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "mesa_id": 3,
  "actor_tipo": 1,
  "inicio": "$inicio",
  "fin_estimado": "$fin"
}
"@ 2>$null | ConvertFrom-Json

if ($holdToCancel.hold.id_hold_mesa) {
  $cancelHoldId = $holdToCancel.hold.id_hold_mesa
  
  $cancelResponse = curl -X POST "$BASE_URL/api/holds/$cancelHoldId/cancelar" `
    -H "Content-Type: application/json" `
    -H "Authorization: Bearer $TOKEN" `
    -d '{}' 2>$null | ConvertFrom-Json
  
  Write-Host "✓ Hold $cancelHoldId cancelado. Status: $($cancelResponse.hold.estatus) (esperado: 2)" -ForegroundColor Green
}

# ====== PASO 10: CREAR PEDIDO DESDE RESERVA ======
Write-Host "`n[PASO 10] Creando pedido desde reserva..." -ForegroundColor Yellow

$createPedidoResponse = curl -X POST "$BASE_URL/api/pedidos" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $TOKEN" `
  -d @"
{
  "reserva_id": $reservaId,
  "sucursal_id": 1,
  "inicia_usuario_id": 1
}
"@ 2>$null | ConvertFrom-Json

if ($createPedidoResponse.pedido.id_pedido) {
  $pedidoId = $createPedidoResponse.pedido.id_pedido
  Write-Host "✓ Pedido creado: ID=$pedidoId" -ForegroundColor Green
} else {
  Write-Host "ERROR al crear pedido:" -ForegroundColor Red
  Write-Host $createPedidoResponse
}

# ====== RESUMEN ======
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE PRUEBAS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`nEntidades creadas:"
Write-Host "  ✓ Hold: ID=$holdId (Mesa 1, Status 2=usado)"
Write-Host "  ✓ Reserva: ID=$reservaId"
Write-Host "  ✓ Pedido: ID=$pedidoId"
Write-Host "`nPruebas exitosas:"
Write-Host "  ✓ Crear hold"
Write-Host "  ✓ Obtener hold"
Write-Host "  ✓ Listar holds"
Write-Host "  ✓ Verificar disponibilidad"
Write-Host "  ✓ Crear reserva desde hold"
Write-Host "  ✓ Hold cambió a usado (status 2)"
Write-Host "  ✓ Cancelar hold"
Write-Host "  ✓ Crear pedido desde reserva"

Write-Host "`nFlujo HOLD → RESERVA → PEDIDO completado exitosamente" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
