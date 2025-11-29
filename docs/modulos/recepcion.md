# Módulo Recepción - Reservas

## Descripción
El módulo de Recepción permite al personal de recepción gestionar reservas para clientes que llegan al restaurante sin cuenta en Cuisine. El recepcionista crea reservas "huérfanas" (sin `cliente_id`), gestiona llegadas y asigna mesas.

---

## ⏱️ Contador de 3 Minutos

La pantalla de reserva debe mostrar un **contador regresivo de 3 minutos** (visual) para indicar cuánto tiempo le queda al recepcionista para completar la reserva antes de que expire el Hold. Similar a las aplicaciones de cine al seleccionar asientos.

**Comportamiento:**
- Al crear el Hold, iniciar contador de 3:00
- Mostrar tiempo restante visualmente (ej: "02:45")
- Al llegar a 0:00, el Hold expira automáticamente
- Si cambia de mesa, reiniciar contador con nuevo Hold

---

## Flujo Completo de Reserva

```
1. Recepcionista lista mesas disponibles
   GET /api/mesas?sucursal_id=1

2. Selecciona mesa → Crea Hold (inicia contador 3 min)
   POST /api/holds

3. Si cambia de mesa → Cancela Hold anterior, crea nuevo
   POST /api/holds/{id}/cancelar
   POST /api/holds

4. Completa datos → Crea Reserva (huérfana)
   POST /api/reservas

5. Cliente llega → Inicia reserva
   POST /api/reservas/{id}/iniciar

6. Cliente termina → Completa reserva
   POST /api/reservas/{id}/completar
```

---

## Sistema de Estados

### Estados de Hold
| estatus | Display | Descripción |
|---------|---------|-------------|
| 1 | Activo | Hold vigente, mesa bloqueada |
| 2 | Confirmado | Hold confirmado, reserva creada |
| 3 | Expirado | TTL de 3 min agotado |

### Estados de Reserva
| estatus | Display | Descripción |
|---------|---------|-------------|
| 1 | Programada | Reserva confirmada, esperando cliente |
| 2 | EnCurso | Cliente llegó y está en mesa |
| 3 | Completada | Cliente terminó |
| 4 | NoShow | Cliente no se presentó |
| 5 | Cancelada | Reserva cancelada |

---

## Endpoints de Mesas

### Listar Mesas de Sucursal
```
GET /api/mesas?sucursal_id=1&solo_activas=true
Authorization: Bearer {token}
```

**Query Parameters:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `sucursal_id` | integer | - | Filtrar por sucursal |
| `area_id` | integer | - | Filtrar por área |
| `solo_activas` | boolean | true | Solo mesas activas |
| `busqueda` | string | - | Buscar por código |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_mesa": 5,
      "area_id": 1,
      "codigo_mesa": "MES-20251122143000",
      "capacidad": 4,
      "es_activa": true,
      "estatus_actual": 1,
      "estatus_display": "Disponible"
    }
  ],
  "total": 5
}
```

**Estados de Mesa:**
| estatus_actual | Display |
|----------------|---------|
| 1 | Disponible |
| 2 | Ocupada |
| 3 | En Limpieza |
| 4 | Fuera Servicio |

---

## Endpoints de Holds

### Crear Hold (Al seleccionar mesa)
```
POST /api/holds
Authorization: Bearer {token}
Content-Type: application/json

{
  "mesa_id": 5,
  "actor_tipo": 2,
  "inicio": "2025-11-28 04:22:00",
  "horas": 4,
  "ttl_minutes": 3,
  "notas": "Reserva telefónica"
}
```

**Request Body:**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `mesa_id` | integer | ✅ | ID de la mesa a bloquear |
| `actor_tipo` | integer | ✅ | 1=Cliente, 2=Recepcionista |
| `inicio` | string | ✅ | Fecha/hora inicio (yyyy-mm-dd hh:mm:ss) |
| `horas` | integer | ✅ | Duración estimada en horas |
| `ttl_minutes` | integer | ❌ | Minutos antes de expirar (default: 3) |
| `notas` | string | ❌ | Notas adicionales |

**Response (201):**
```json
{
  "message": "Hold creado exitosamente",
  "hold": {
    "id_hold_mesa": 119,
    "mesa_id": 5,
    "estatus": 1,
    "actor_usuario_id": 4,
    "inicio": "2025-11-28T04:22:00",
    "fin_estimado": "2025-11-28T08:22:00",
    "fechahora_expiracion": "2025-11-28T04:25:00"
  }
}
```

> **Importante:** `fechahora_expiracion` indica cuándo expira el Hold (3 min después de crearlo)

---

### Cancelar Hold (Al cambiar selección de mesa)
```
POST /api/holds/{hold_id}/cancelar
Authorization: Bearer {token}
Content-Type: application/json

{
  "motivo": "Cambio de mesa"
}
```

**Response (200):**
```json
{
  "message": "Hold cancelado exitosamente",
  "hold": {
    "id_hold_mesa": 119,
    "mesa_id": 5,
    "estatus": 2
  }
}
```

---

### Verificar Disponibilidad
```
POST /api/holds/disponibilidad
Authorization: Bearer {token}
Content-Type: application/json

{
  "mesa_id": 5,
  "inicio": "2025-11-28T04:22:00",
  "fin_estimado": "2025-11-28T08:22:00"
}
```

**Response (200):**
```json
{
  "disponible": true,
  "mensaje": "Mesa disponible en el horario solicitado"
}
```

---

## Endpoints de Reservas

### Crear Reserva
```
POST /api/reservas
Authorization: Bearer {token}
Content-Type: application/json

{
  "cliente_id": null,
  "fin_estimado": "2025-11-28 08:22:00",
  "hold_id": 119,
  "inicio": "2025-11-28 04:22:00",
  "notas": "Mesa para 4, cumpleaños",
  "recepcionista_id": 4,
  "tolerancia_min": 5
}
```

**Request Body:**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `cliente_id` | integer | ❌ | Siempre `null` para recepcionista |
| `inicio` | string | ✅ | Fecha/hora inicio (yyyy-mm-dd hh:mm:ss) |
| `fin_estimado` | string | ✅ | Fecha/hora fin estimado |
| `hold_id` | integer | ✅ | ID del Hold creado previamente |
| `recepcionista_id` | integer | ✅ | ID del recepcionista que crea |
| `tolerancia_min` | integer | ❌ | Minutos de tolerancia (default: 15) |
| `notas` | string | ❌ | Nombre del cliente, ocasión, etc. |

**Response (201):**
```json
{
  "message": "Reserva creada exitosamente",
  "reserva": {
    "id_reserva": 10,
    "cliente_id": null,
    "recepcionista_id": 4,
    "inicio": "2025-11-28T04:22:00",
    "fin_estimado": "2025-11-28T08:22:00",
    "estatus": 1,
    "estatus_display": "Programada",
    "tolerancia_min": 5,
    "notas": "Mesa para 4, cumpleaños",
    "hold_id": 119,
    "puede_iniciar": false
  }
}
```

---

### Listar Reservas
```
POST /api/reservas/listar
Authorization: Bearer {token}
Content-Type: application/json

{
  "sucursal_id": 1,
  "estatus": 1,
  "fecha_desde": "2025-11-28 00:00:00",
  "fecha_hasta": "2025-11-28 23:59:59"
}
```

**Request Body (todos opcionales):**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sucursal_id` | integer | Filtrar por sucursal |
| `estatus` | integer | Filtrar por estatus (1-5) |
| `fecha_desde` | string | Inicio del rango (yyyy-mm-dd hh:mm:ss) |
| `fecha_hasta` | string | Fin del rango (yyyy-mm-dd hh:mm:ss) |

**Response (200):**
```json
{
  "reservas": [
    {
      "id_reserva": 10,
      "cliente_id": null,
      "recepcionista_id": 4,
      "inicio": "2025-11-28T04:22:00",
      "fin_estimado": "2025-11-28T08:22:00",
      "estatus": 1,
      "estatus_display": "Programada",
      "notas": "Mesa para 4, cumpleaños",
      "puede_iniciar": true
    }
  ],
  "total": 1
}
```

---

### Obtener Reserva
```
GET /api/reservas/{reserva_id}
Authorization: Bearer {token}
```

---

### Iniciar Reserva (Cliente Llegó)
```
POST /api/reservas/{reserva_id}/iniciar
Authorization: Bearer {token}
```

**Descripción:** Marca llegada del cliente. Estatus 1 → 2.

**Validaciones:**
- Reserva en estado Programada (1)
- Hora actual >= (inicio - tolerancia_min)

**Response (200):**
```json
{
  "message": "Reserva iniciada exitosamente",
  "reserva": {
    "id_reserva": 10,
    "estatus": 2,
    "estatus_display": "En Curso"
  }
}
```

---

### Completar Reserva
```
POST /api/reservas/{reserva_id}/completar
Authorization: Bearer {token}
```

**Descripción:** Cliente terminó y se va. Estatus 2 → 3.

---

### Cancelar Reserva
```
POST /api/reservas/{reserva_id}/cancelar
Authorization: Bearer {token}
Content-Type: application/json

{
  "motivo": "Cliente llamó para cancelar"
}
```

**Estados permitidos:** 1 (Programada) o 2 (EnCurso)

---

### Marcar No Show
```
POST /api/reservas/{reserva_id}/no-show
Authorization: Bearer {token}
```

**Descripción:** Cliente no llegó después de tolerancia. Estatus 1 → 4.

---

## Campo `puede_iniciar`

Indica si la reserva está en ventana de tiempo para iniciar:

```
puede_iniciar = (ahora >= inicio - tolerancia_min)
```

**Ejemplo:** Reserva 19:00, tolerancia 5 min → puede iniciar desde 18:55

---

## Notas de Implementación

- **Reservas huérfanas:** `cliente_id = null` para clientes sin cuenta
- **Hold obligatorio:** Siempre crear Hold antes de reserva
- **TTL de 3 minutos:** El Hold expira automáticamente si no se completa la reserva
- **Contador visual:** Mostrar tiempo restante del Hold en la UI
- **Cambio de mesa:** Cancelar Hold anterior antes de crear uno nuevo
- **Notas:** Usar para identificar al cliente (nombre, teléfono, ocasión)
- **Timezone:** `America/Mexico_City`
- **Formato fechas:** `yyyy-mm-dd hh:mm:ss`
