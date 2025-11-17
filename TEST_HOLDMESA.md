# Guía de Pruebas - HoldMesa Endpoints

## Preliminares

### 1. Asegúrate que el servidor está corriendo
```powershell
python app.py
# Debe ver: Running on http://0.0.0.0:5000
```

### 2. Obtén un Token JWT válido
Primero login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d {
    "email": "admin@example.com",
    "password": "password123"
  }
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id_usuario": 1,
    "nombre": "Admin User",
    "email": "admin@example.com"
  }
}
```

**Guarda el token en una variable:**
```powershell
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
$HEADER = "Authorization: Bearer $TOKEN"
```

---

## Endpoint 1: POST /api/holds - Crear Hold

**Descripción:** Crea un hold temporal de 3 minutos para reservar una mesa.

### Caso 1.1: Crear hold básico (Cliente llegó a recepción)
```bash
curl -X POST http://localhost:5000/api/holds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 5,
    "actor_tipo": 2,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00",
    "ttl_minutes": 3,
    "notas": "Cliente esperando para cenar"
  }
```

**Respuesta esperada (201):**
```json
{
  "message": "Hold creado exitosamente",
  "hold": {
    "id_hold_mesa": 1,
    "mesa_id": 5,
    "estatus": 1,
    "actor_usuario_id": 1,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00",
    "fechahora_expiracion": "2025-11-17T19:03:00",
    "notas": "Cliente esperando para cenar"
  }
}
```

### Caso 1.2: Mesa no disponible (conflicto con otra reserva)
```bash
curl -X POST http://localhost:5000/api/holds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 5,
    "actor_tipo": 2,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00"
  }
```

**Respuesta esperada (409):**
```json
{
  "error": "Mesa 5 no está disponible en ese rango de fechas"
}
```

### Caso 1.3: Validación - mesa no existe
```bash
curl -X POST http://localhost:5000/api/holds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 9999
  }
```

**Respuesta esperada (400):**
```json
{
  "error": "Datos inválidos",
  "detalles": {
    "mesa_id": ["Mesa 9999 no existe"]
  }
}
```

---

## Endpoint 2: GET /api/holds/{hold_id} - Obtener Hold

**Descripción:** Obtiene los detalles de un hold específico.

### Caso 2.1: Obtener hold existente
```bash
curl -X GET http://localhost:5000/api/holds/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta esperada (200):**
```json
{
  "id_hold_mesa": 1,
  "mesa_id": 5,
  "estatus": 1,
  "actor_usuario_id": 1,
  "inicio": "2025-11-17T19:00:00",
  "fin_estimado": "2025-11-17T21:00:00",
  "fechahora_expiracion": "2025-11-17T19:03:00",
  "notas": "Cliente esperando para cenar"
}
```

### Caso 2.2: Hold no existe
```bash
curl -X GET http://localhost:5000/api/holds/9999 \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta esperada (404):**
```json
{
  "error": "Hold 9999 no existe"
}
```

---

## Endpoint 3: GET /api/holds?mesa_id=X - Listar Holds Activos

**Descripción:** Lista todos los holds activos (no expirados ni cancelados).

### Caso 3.1: Listar todos los holds activos
```bash
curl -X GET "http://localhost:5000/api/holds" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta esperada (200):**
```json
{
  "holds": [
    {
      "id_hold_mesa": 1,
      "mesa_id": 5,
      "estatus": 1,
      "actor_usuario_id": 1,
      "inicio": "2025-11-17T19:00:00",
      "fin_estimado": "2025-11-17T21:00:00",
      "fechahora_expiracion": "2025-11-17T19:03:00"
    },
    {
      "id_hold_mesa": 2,
      "mesa_id": 7,
      "estatus": 1,
      "actor_usuario_id": 1,
      "inicio": "2025-11-17T20:00:00",
      "fin_estimado": "2025-11-17T22:00:00",
      "fechahora_expiracion": "2025-11-17T20:03:00"
    }
  ],
  "total": 2
}
```

### Caso 3.2: Filtrar holds activos por mesa
```bash
curl -X GET "http://localhost:5000/api/holds?mesa_id=5" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta esperada (200):**
```json
{
  "holds": [
    {
      "id_hold_mesa": 1,
      "mesa_id": 5,
      "estatus": 1,
      ...
    }
  ],
  "total": 1
}
```

### Caso 3.3: Sin holds activos
```bash
curl -X GET "http://localhost:5000/api/holds" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta esperada (200):**
```json
{
  "holds": [],
  "total": 0
}
```

---

## Endpoint 4: POST /api/holds/{hold_id}/cancelar - Cancelar Hold

**Descripción:** Cancela un hold activo (estatus 1 → 2).

### Caso 4.1: Cancelar hold existente
```bash
curl -X POST http://localhost:5000/api/holds/1/cancelar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "motivo": "Cliente decidió no comer aquí"
  }
```

**Respuesta esperada (200):**
```json
{
  "message": "Hold cancelado exitosamente",
  "hold": {
    "id_hold_mesa": 1,
    "mesa_id": 5,
    "estatus": 2,
    "actor_usuario_id": 1,
    "notas": "Cliente esperando para cenar",
    "motivo_cancelacion": "Cliente decidió no comer aquí"
  }
}
```

### Caso 4.2: Cancelar hold ya expirado
Espera 4 minutos desde su creación, luego intenta cancelar:
```bash
curl -X POST http://localhost:5000/api/holds/1/cancelar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {}
```

**Respuesta esperada (400):**
```json
{
  "error": "Hold 1 no está activo (estatus=3)"
}
```

### Caso 4.3: Hold no existe
```bash
curl -X POST http://localhost:5000/api/holds/9999/cancelar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {}
```

**Respuesta esperada (404):**
```json
{
  "error": "Hold 9999 no existe"
}
```

---

## Endpoint 5: POST /api/holds/disponibilidad - Verificar Disponibilidad

**Descripción:** Verifica si una mesa está disponible en un rango de fechas SIN crear hold.

### Caso 5.1: Mesa disponible
```bash
curl -X POST http://localhost:5000/api/holds/disponibilidad \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 10,
    "inicio": "2025-11-17T22:00:00",
    "fin_estimado": "2025-11-18T00:00:00"
  }
```

**Respuesta esperada (200):**
```json
{
  "disponible": true,
  "mensaje": "Mesa disponible"
}
```

### Caso 5.2: Mesa NO disponible (hay hold)
Si la mesa 5 ya tiene un hold activo:
```bash
curl -X POST http://localhost:5000/api/holds/disponibilidad \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 5,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00"
  }
```

**Respuesta esperada (200):**
```json
{
  "disponible": false,
  "mensaje": "Mesa no disponible (hay hold o reserva activa)"
}
```

### Caso 5.3: Validación - mesa no existe
```bash
curl -X POST http://localhost:5000/api/holds/disponibilidad \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 9999,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00"
  }
```

**Respuesta esperada (400):**
```json
{
  "error": "Mesa 9999 no existe"
}
```

---

## Flujo Completo de Prueba: HOLD → RESERVA → PEDIDO

### Paso 1: Crear Hold
```bash
$response = curl -X POST http://localhost:5000/api/holds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "mesa_id": 5,
    "actor_tipo": 2,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00",
    "ttl_minutes": 3
  }

# Extrae hold_id: 1
```

### Paso 2: Verificar Hold está activo (antes de 3 minutos)
```bash
curl -X GET http://localhost:5000/api/holds/1 \
  -H "Authorization: Bearer $TOKEN"
# Debe retornar estatus: 1
```

### Paso 3: Crear Reserva desde Hold
```bash
curl -X POST http://localhost:5000/api/reservas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "cliente_id": 1,
    "inicio": "2025-11-17T19:00:00",
    "fin_estimado": "2025-11-17T21:00:00",
    "hold_id": 1
  }
# Retorna reserva_id: 1
# Hold debe cambiar a estatus 2 (usado)
```

### Paso 4: Verificar Hold cambió a usado
```bash
curl -X GET http://localhost:5000/api/holds/1 \
  -H "Authorization: Bearer $TOKEN"
# Debe retornar estatus: 2
```

### Paso 5: Crear Pedido desde Reserva
```bash
curl -X POST http://localhost:5000/api/pedidos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d {
    "reserva_id": 1,
    "sucursal_id": 1,
    "inicia_usuario_id": 1
  }
# Retorna pedido_id: 1
```

---

## Pruebas de Expiraciones Automáticas

### Test: Hold expira después de 3 minutos

```bash
# 1. Crear hold
$hold = curl -X POST http://localhost:5000/api/holds ...
# hold_id = 1, fechahora_expiracion = 2025-11-17T19:03:00

# 2. Esperar 4 minutos

# 3. Intentar obtener hold
curl -X GET http://localhost:5000/api/holds/1 \
  -H "Authorization: Bearer $TOKEN"
# Debería mostrar estatus: 3 (Expirado)
```

### Test: El scheduler actualiza holds expirados automáticamente

El scheduler está programado para ejecutarse cada minuto y marcar holds como expirados.

Verifica los logs:
```
[INFO] HoldMesaScheduler: Actualizando holds expirados...
[INFO] HoldMesaScheduler: Hold 1 marcado como expirado
```

---

## Notas sobre TTL (Time To Live)

- **Default TTL**: 3 minutos (180 segundos)
- **Configurable**: Puedes pasar `ttl_minutes` al crear el hold
- **Actualización automática**: El scheduler verifica cada minuto qué holds expiraron
- **Estados posibles**:
  - `1` = Activo
  - `2` = Cancelado
  - `3` = Expirado (automático después de TTL)

---

## Checklist de Pruebas

### HoldMesa Básico
- [ ] Crear hold → status 201
- [ ] Obtener hold existente → status 200
- [ ] Listar holds activos → status 200
- [ ] Cancelar hold activo → status 200
- [ ] Verificar disponibilidad → status 200

### Validaciones
- [ ] Crear hold sin mesa_id → error 400
- [ ] Obtener hold no existente → error 404
- [ ] Cancelar hold ya cancelado → error 400
- [ ] Mesa no activa → error 400

### Expiración Automática
- [ ] Hold expira después de 3 minutos
- [ ] El scheduler marca como expirado (status 3)
- [ ] No se puede cancelar hold expirado

### Flujo Integrado
- [ ] HOLD creado
- [ ] RESERVA creada desde HOLD
- [ ] Hold cambia a status 2 (usado)
- [ ] PEDIDO creado desde RESERVA

