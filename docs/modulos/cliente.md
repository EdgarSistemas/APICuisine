# 📱 Módulo Cliente

Documentación de endpoints para la **app móvil del cliente**. Este módulo permite a los clientes gestionar sus reservas, realizar pedidos (en sitio y para llevar), ver sus cupones disponibles y calificar el servicio.

> **Nota**: Todos los endpoints requieren autenticación JWT, excepto los marcados como públicos.

> ⚠️ **Importante**: El cliente **NO está ligado a una sucursal**. Debe elegir explícitamente la sucursal y mesa donde desea reservar.

---

## Tabla de Contenidos

1. [Catálogos (Sucursales, Áreas, Mesas)](#1-catálogos)
2. [Menú (Categorías, Productos, Combos)](#2-menú)
3. [Reservas](#3-reservas)
4. [Pedidos](#4-pedidos)
5. [CRM - Cupones](#5-crm---cupones)
6. [Calificaciones y Mejoras](#6-calificaciones-y-mejoras)

---

## 1. Catálogos

El cliente debe consultar estos endpoints para **elegir la sucursal y mesa** donde desea hacer su reserva.

### 1.1 Listar Sucursales Activas

```
GET /api/sucursales/activas
```

> 🔓 **Endpoint público** - No requiere autenticación

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_sucursal": 1,
      "codigo_sucursal": "SUC-001",
      "nombre": "Sucursal Centro",
      "telefono": "555-123-4567",
      "direccion": "Av. Principal #123",
      "es_activa": true
    },
    {
      "id_sucursal": 2,
      "codigo_sucursal": "SUC-002",
      "nombre": "Sucursal Norte",
      "telefono": "555-987-6543",
      "direccion": "Blvd. Norte #456",
      "es_activa": true
    }
  ]
}
```

---

### 1.2 Obtener Sucursal por ID

```
GET /api/sucursales/{sucursal_id}
```

---

### 1.3 Listar Áreas por Sucursal

```
GET /api/areas?sucursal_id={sucursal_id}
```

**Query params:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `sucursal_id` | int | ✅ | ID de la sucursal |
| `solo_activas` | bool | ❌ | Solo áreas activas (default: true) |

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_area": 1,
      "sucursal_id": 1,
      "nombre": "Salón Principal",
      "descripcion": "Área principal con vista al jardín",
      "es_activa": true
    },
    {
      "id_area": 2,
      "sucursal_id": 1,
      "nombre": "Terraza",
      "descripcion": "Área al aire libre",
      "es_activa": true
    }
  ],
  "total": 2
}
```

---

### 1.4 Listar Mesas por Sucursal/Área

```
GET /api/mesas?sucursal_id={sucursal_id}
```

**Query params:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `sucursal_id` | int | ✅ | ID de la sucursal |
| `area_id` | int | ❌ | Filtrar por área específica |
| `solo_activas` | bool | ❌ | Solo mesas activas (default: true) |

**Respuesta (200):**
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
  "total": 1
}
```

### Estados de Mesa

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Disponible | `1` | Mesa libre para reservar |
| Ocupada | `2` | Mesa en uso |
| En Limpieza | `3` | Mesa siendo preparada |
| Fuera de Servicio | `4` | Mesa no disponible |

---

## 2. Menú

El cliente consulta estos endpoints para ver el **menú disponible** y agregar items a su pedido.

### 2.1 Listar Categorías del Menú

```
GET /api/categorias
```

> 🔓 **Endpoint público**

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_categoria": 1,
      "nombre": "Entradas",
      "descripcion": "Platillos para compartir",
      "es_activa": true
    },
    {
      "id_categoria": 2,
      "nombre": "Platos Fuertes",
      "descripcion": "Especialidades de la casa",
      "es_activa": true
    },
    {
      "id_categoria": 3,
      "nombre": "Bebidas",
      "descripcion": "Refrescos y bebidas",
      "es_activa": true
    }
  ]
}
```

---

### 2.2 Listar Productos

```
GET /api/productos
```

> 🔓 **Endpoint público**

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_producto": 10,
      "categoria_id": 2,
      "codigo": "HAM001",
      "nombre": "Hamburguesa Clásica",
      "descripcion": "Carne de res 200g con queso cheddar",
      "imagen_url": "https://...",
      "precio": 150.00,
      "es_activo": true
    },
    {
      "id_producto": 15,
      "categoria_id": 2,
      "codigo": "PIZ001",
      "nombre": "Pizza Pepperoni",
      "descripcion": "Pizza mediana con pepperoni",
      "imagen_url": "https://...",
      "precio": 220.00,
      "es_activo": true
    }
  ]
}
```

---

### 2.3 Obtener Producto por ID

```
GET /api/productos/{producto_id}
```

---

### 2.4 Listar Combos

```
GET /api/combos
```

> 🔓 **Endpoint público**

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_combo": 5,
      "nombre": "Combo Familiar",
      "descripcion": "2 hamburguesas + 2 bebidas + papas grandes",
      "imagen_url": "https://...",
      "precio": 350.00,
      "es_activo": true,
      "productos": [
        {
          "producto_id": 10,
          "nombre": "Hamburguesa Clásica",
          "cantidad": 2
        },
        {
          "producto_id": 20,
          "nombre": "Refresco",
          "cantidad": 2
        }
      ]
    }
  ]
}
```

---

### 2.5 Obtener Combo por ID

```
GET /api/combos/{combo_id}
```

---

## 3. Reservas

El cliente **elige la sucursal, luego el área, y finalmente la mesa**, después crea su reserva usando el sistema de Hold.

### 3.1 Flujo Completo de Reserva

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 1. ELEGIR   │ ──▶│ 2. ELEGIR   │ ──▶│ 3. ELEGIR   │ ──▶│ 4. VERIFICAR│ ──▶│ 5. CREAR    │ ──▶│ 6. CREAR    │
│   SUCURSAL  │    │    ÁREA     │    │    MESA     │    │   DISPONIB. │    │    HOLD     │    │   RESERVA   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │                  │                  │
     ▼                   ▼                  ▼                  ▼                  ▼                  ▼
GET /sucursales    GET /areas?        GET /mesas?       POST /holds/      POST /holds       POST /reservas
   /activas        sucursal_id=X    sucursal_id=X&    disponibilidad
                                      area_id=Y
```

### 3.2 Paso a Paso del Flujo

#### Paso 1: Elegir Sucursal
```
GET /api/sucursales/activas
```
El cliente ve la lista de sucursales disponibles y selecciona una.

#### Paso 2: Elegir Área
```
GET /api/areas?sucursal_id={sucursal_id}
```
Con la sucursal seleccionada, el cliente ve las áreas disponibles (Salón, Terraza, VIP, etc.).

#### Paso 3: Elegir Mesa
```
GET /api/mesas?sucursal_id={sucursal_id}&area_id={area_id}
```
Con el área seleccionada, el cliente ve las mesas disponibles con su capacidad y estado actual.

#### Paso 4: Verificar Disponibilidad de Mesa

```
POST /api/holds/disponibilidad
```

**Body:**
```json
{
  "mesa_id": 5,
  "inicio": "2025-12-15T19:00:00",
  "fin_estimado": "2025-12-15T21:00:00"
}
```

**Respuesta (200) - Disponible:**
```json
{
  "disponible": true,
  "mensaje": "Mesa disponible en el horario solicitado"
}
```

**Respuesta (200) - No Disponible:**
```json
{
  "disponible": false,
  "mensaje": "Mesa no disponible. Ya existe un hold o reserva activa en ese horario."
}
```

---

### 3.3 Sistema de Hold (Paso 5)

Antes de crear una reserva, se debe **bloquear la mesa temporalmente** (3 minutos por defecto).

#### Crear Hold en Mesa

```
POST /api/holds
```

**Body:**
```json
{
  "mesa_id": 5,
  "actor_tipo": 1,
  "inicio": "2025-12-15 19:00:00",
  "horas": 2,
  "ttl_minutes": 3,
  "notas": "Mesa cerca de ventana"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `mesa_id` | int | ✅ | ID de la mesa a reservar |
| `actor_tipo` | int | ✅ | `1` = Cliente, `2` = Recepcionista |
| `inicio` | string | ✅ | Fecha/hora inicio `yyyy-mm-dd hh:mm:ss` |
| `horas` | int | ✅ | Duración estimada en horas |
| `ttl_minutes` | int | ❌ | Minutos antes de expirar (default: 3, max: 30) |
| `notas` | string | ❌ | Notas adicionales |

**Respuesta (201):**
```json
{
  "message": "Hold creado exitosamente",
  "hold": {
    "id_hold_mesa": 123,
    "mesa_id": 5,
    "actor_tipo": 1,
    "actor_usuario_id": 45,
    "estatus": 1,
    "inicio": "2025-12-15T19:00:00",
    "fin_estimado": "2025-12-15T21:00:00",
    "expires_at": "2025-12-15T15:03:00",
    "horas": 2
  }
}
```

> ⏱️ **TTL de 3 minutos**: Si no se crea la reserva, el hold expira automáticamente.

#### Estados del Hold

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Activo | `1` | Hold vigente, esperando confirmación |
| Confirmado | `2` | Hold convertido a reserva |
| Expirado | `3` | TTL cumplido sin confirmar |
| Cancelado | `4` | Cancelado por usuario |

---

#### Confirmar Hold

```
POST /api/holds/{hold_id}/confirmar
```

> ⚠️ **Importante**: Confirmar el hold antes de crear la reserva.

**Validaciones:**
- Hold existe
- Hold está activo (estatus=1)
- Hold no ha expirado

**Respuesta (200):**
```json
{
  "message": "Hold confirmado. Ahora puedes crear la reserva.",
  "hold": {
    "id_hold_mesa": 123,
    "estatus": 2,
    "mesa_id": 5
  },
  "tiempo_restante_min": 2.5
}
```

---

#### Cancelar Hold

```
POST /api/holds/{hold_id}/cancelar
```

**Body (opcional):**
```json
{
  "motivo": "Cambio de planes"
}
```

**Respuesta (200):**
```json
{
  "message": "Hold cancelado",
  "hold": {
    "id_hold_mesa": 123,
    "estatus": 4
  }
}
```

---

### 3.4 Crear Reserva (Paso 6)

```
POST /api/reservas
```

**Body:**
```json
{
  "cliente_id": 45,
  "recepcionista_id": null,
  "inicio": "2025-12-15 19:00:00",
  "fin_estimado": "2025-12-15 21:00:00",
  "tolerancia_min": 15,
  "notas": "Cumpleaños, mesa cerca de ventana",
  "hold_id": 123
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `cliente_id` | int | ❌ | ID del cliente (se obtiene del JWT) |
| `recepcionista_id` | int | ❌ | NULL si es desde app cliente |
| `inicio` | string | ✅ | Fecha/hora inicio `yyyy-mm-dd hh:mm:ss` |
| `fin_estimado` | string | ✅ | Fecha/hora fin estimada |
| `tolerancia_min` | int | ❌ | Minutos de tolerancia (default: 15, max: 120) |
| `notas` | string | ❌ | Notas adicionales (max: 300 chars) |
| `hold_id` | int | ⭐ | ID del hold confirmado (recomendado) |

**Respuesta (201):**
```json
{
  "success": true,
  "data": {
    "id_reserva": 789,
    "cliente_id": 45,
    "inicio": "2025-12-15T19:00:00",
    "fin_estimado": "2025-12-15T21:00:00",
    "estatus": 1,
    "tolerancia_min": 15,
    "notas": "Cumpleaños, mesa cerca de ventana",
    "hold_id": 123,
    "created_at": "2025-12-10T14:30:00"
  }
}
```

---

### 3.5 Estados de Reserva

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Programada | `1` | Reserva confirmada, esperando cliente |
| En Curso | `2` | Cliente llegó, ocupando mesa |
| Completada | `3` | Cliente terminó y se fue |
| No Show | `4` | Cliente no llegó en tiempo de tolerancia |
| Cancelada | `5` | Cancelada por cliente o sistema |

---

### 3.6 Consultar Reserva

```
GET /api/reservas/{reserva_id}
```

**Respuesta (200):**
```json
{
  "success": true,
  "data": {
    "id_reserva": 789,
    "cliente_id": 45,
    "inicio": "2025-12-15T19:00:00",
    "fin_estimado": "2025-12-15T21:00:00",
    "estatus": 1,
    "estatus_display": "Programada",
    "tolerancia_min": 15,
    "notas": "Cumpleaños",
    "hold_id": 123,
    "puede_iniciar": false,
    "created_at": "2025-12-10T14:30:00"
  }
}
```

---

### 3.7 Listar Mis Reservas

```
POST /api/reservas/listar
```

**Body:**
```json
{
  "cliente_id": 45,
  "estatus": 1,
  "fecha_desde": "2025-12-01T00:00:00",
  "fecha_hasta": "2025-12-31T23:59:59"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `cliente_id` | int | ❌ | Filtrar por cliente |
| `sucursal_id` | int | ❌ | Filtrar por sucursal |
| `estatus` | int | ❌ | Filtrar por estado |
| `fecha_desde` | string | ❌ | Desde fecha (ISO format) |
| `fecha_hasta` | string | ❌ | Hasta fecha (ISO format) |

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_reserva": 789,
      "inicio": "2025-12-15T19:00:00",
      "estatus": 1,
      "estatus_display": "Programada"
    },
    {
      "id_reserva": 790,
      "inicio": "2025-12-20T20:00:00",
      "estatus": 1,
      "estatus_display": "Programada"
    }
  ]
}
```

---

### 3.8 Cancelar Reserva

```
POST /api/reservas/{reserva_id}/cancelar
```

**Body (opcional):**
```json
{
  "motivo": "Cambio de planes"
}
```

**Validaciones:**
- Solo se pueden cancelar reservas en estatus `1` (Programada) o `2` (En Curso)

**Respuesta (200):**
```json
{
  "success": true,
  "data": {
    "id_reserva": 789,
    "estatus": 5,
    "estatus_display": "Cancelada"
  }
}
```

---

## 4. Pedidos

El cliente puede hacer **su propio pedido** tanto en sitio como para llevar.

### 4.1 Estados del Sistema

#### Estados de Pedido (`estado_pedido`)

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Iniciado | `0` | Pedido recién creado, agregando items |
| Completo | `3` | Usuario cerró el pedido |
| Cancelado | `4` | Pedido cancelado |
| Pagado | `5` | Pedido pagado |

#### Estados de Item (`estatus_detalle`)

| Estado | Valor | Descripción |
|--------|-------|-------------|
| En Cocina | `1` | Item creado, inventario consumido |
| Listo | `2` | Preparado por cocina |
| Completo | `3` | Entregado al cliente |
| Cancelado | `4` | Item cancelado |
| Pagado | `5` | Item pagado |

---

### 4.2 Flujo de Pedidos

```
DINE-IN (En sitio):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ RESERVA  │ ──▶│ CREAR    │ ──▶│ AGREGAR  │ ──▶│ COMPLETAR│ ──▶│ PAGAR    │
│ ACTIVA   │    │ PEDIDO   │    │ ITEMS    │    │ PEDIDO   │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
    (1-2)           (0)            (0)             (3)            (5)

TAKEAWAY (Para llevar):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────────────┐
│ CREAR    │ ──▶│ AGREGAR  │ ──▶│ COCINA   │ ──▶│ AUTO-PAGO      │
│ PEDIDO   │    │ ITEMS    │    │ PREPARA  │    │ (todos listos) │
└──────────┘    └──────────┘    └──────────┘    └────────────────┘
    (0)            (0)           (1→2)              (5)
```

---

### 4.3 Crear Pedido Dine-in (En sitio)

```
POST /api/pedidos
```

> ⚠️ **REQUIERE** reserva activa (estatus 1 o 2)

**Body:**
```json
{
  "sucursal_id": 1,
  "cliente_id": 45,
  "canal": 2,
  "reserva_id": 789,
  "notas": "Sin picante",
  "items": [
    {
      "producto_id": 10,
      "cantidad": 2,
      "notas": "Extra queso"
    },
    {
      "combo_id": 5,
      "cantidad": 1
    }
  ]
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `sucursal_id` | int | ✅ | ID de la sucursal |
| `cliente_id` | int | ✅ | ID del cliente |
| `canal` | int | ✅ | `1`=PWA, `2`=Móvil, `3`=Presencial |
| `reserva_id` | int | ✅ | ID de reserva activa |
| `notas` | string | ❌ | Notas del pedido |
| `items` | array | ❌ | Items iniciales (opcional) |

**Respuesta (201):**
```json
{
  "mensaje": "Pedido creado - items en cocina, inventario consumido",
  "pedido": {
    "id_pedido": 100,
    "sucursal_id": 1,
    "cliente_id": 45,
    "tipo_pedido": 1,
    "canal": 2,
    "estado_pedido": 0,
    "reserva_id": 789,
    "mesa_id": 5,
    "total": 500.00,
    "items": [
      {
        "id_pedido_item": 1,
        "producto_id": 10,
        "producto_nombre": "Hamburguesa Clásica",
        "cantidad": 2,
        "precio_unit": 150.00,
        "subtotal": 300.00,
        "estatus_detalle": 1,
        "consumo_exitoso": true
      }
    ]
  }
}
```

---

### 4.4 Crear Pedido Takeaway (Para llevar)

```
POST /api/pedidos/para-llevar
```

> ✅ **NO requiere reserva** - Crea una reserva interna automáticamente

**Body:**
```json
{
  "sucursal_id": 1,
  "cliente_id": 45,
  "canal": 2,
  "notas": "Empacar por separado",
  "items": [
    {
      "producto_id": 10,
      "cantidad": 2
    },
    {
      "producto_id": 15,
      "cantidad": 1
    }
  ]
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `sucursal_id` | int | ✅ | ID de la sucursal |
| `cliente_id` | int | ✅ | ID del cliente (**obligatorio**) |
| `canal` | int | ✅ | `1`=PWA, `2`=Móvil, `3`=Presencial |
| `notas` | string | ❌ | Notas del pedido |
| `items` | array | ❌ | Items iniciales |

**Respuesta (201):**
```json
{
  "mensaje": "Pedido Takeaway creado - items en cocina, inventario consumido",
  "pedido": {
    "id_pedido": 101,
    "tipo_pedido": 2,
    "estado_pedido": 0,
    "mesa_id": null,
    "items": [...]
  }
}
```

> 🎯 **Auto-pago Takeaway**: Cuando cocina marca **todos los items como Listo (2)**, el pedido se auto-paga a estado `5`.

---

### 4.5 Agregar Item al Pedido

```
POST /api/pedidos/{pedido_id}/items
```

**Body:**
```json
{
  "producto_id": 20,
  "cantidad": 1,
  "notas": "Con hielo"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `producto_id` | int | ⭐ | ID del producto (XOR con combo_id) |
| `combo_id` | int | ⭐ | ID del combo (XOR con producto_id) |
| `cantidad` | int | ✅ | Cantidad |
| `notas` | string | ❌ | Notas del item |

**Validaciones:**
- Pedido debe estar en estado `0` (Iniciado) o `3` (Completo)
- Debe proporcionar `producto_id` **O** `combo_id`, no ambos
- Consume inventario inmediatamente (FIFO por lotes)

**Respuesta (201):**
```json
{
  "message": "Item agregado exitosamente",
  "item": {
    "id_pedido_item": 5,
    "producto_id": 20,
    "producto_nombre": "Refresco",
    "cantidad": 1,
    "precio_unit": 35.00,
    "subtotal": 35.00,
    "estatus_detalle": 1,
    "consumo_exitoso": true
  }
}
```

---

### 4.6 Ver Estado del Pedido

```
GET /api/pedidos/{pedido_id}
```

**Respuesta (200):**
```json
{
  "id_pedido": 100,
  "sucursal_id": 1,
  "cliente_id": 45,
  "tipo_pedido": 1,
  "tipo_pedido_display": "Dine-in",
  "estado_pedido": 0,
  "estado_display": "Iniciado",
  "mesa_id": 5,
  "reserva_id": 789,
  "total": 535.00,
  "notas": "Sin picante",
  "items": [
    {
      "id_pedido_item": 1,
      "producto_nombre": "Hamburguesa Clásica",
      "cantidad": 2,
      "precio_unit": 150.00,
      "subtotal": 300.00,
      "estatus_detalle": 2,
      "estatus_display": "Listo",
      "notas": "Extra queso"
    },
    {
      "id_pedido_item": 2,
      "combo_nombre": "Combo Familiar",
      "cantidad": 1,
      "precio_unit": 200.00,
      "subtotal": 200.00,
      "estatus_detalle": 1,
      "estatus_display": "En Cocina"
    }
  ],
  "created_at": "2025-12-15T19:15:00"
}
```

---

### 4.7 Listar Mis Pedidos

```
POST /api/pedidos/listar
```

**Body:**
```json
{
  "cliente_id": 45,
  "sucursal_id": 1,
  "estado": 0,
  "tipo_pedido": 1,
  "fecha_desde": "2025-12-01",
  "fecha_hasta": "2025-12-31"
}
```

---

### 4.8 Ver Pedidos Activos

```
GET /api/pedidos/activos?sucursal_id=1
```

Retorna pedidos en estado `0` (Iniciado) y `3` (Completo).

---

### 4.9 Completar Pedido

```
PATCH /api/pedidos/{pedido_id}/completar
```

> Cambia estado: `0` → `3`

**Validaciones:**
- Pedido debe estar en estado `0` (Iniciado)
- **Todos los items** deben estar en estado `2` (Listo) o superior

**Respuesta (200):**
```json
{
  "mensaje": "Pedido completado",
  "pedido": {
    "id_pedido": 100,
    "estado_pedido": 3,
    "estado_display": "Completo"
  }
}
```

---

### 4.10 Cancelar Pedido

```
PATCH /api/pedidos/{pedido_id}/cancelar
```

**Body (opcional):**
```json
{
  "comentario": "Cliente cambió de opinión"
}
```

**Validaciones:**
- Solo se pueden cancelar pedidos en estado `0` (Iniciado)

> ⚠️ **NOTA**: Si los items ya consumieron inventario, **NO se revierte** al cancelar.

**Respuesta (200):**
```json
{
  "mensaje": "Pedido cancelado",
  "pedido": {
    "id_pedido": 100,
    "estado_pedido": 4,
    "estado_display": "Cancelado"
  }
}
```

---

## 5. CRM - Cupones

El cliente puede ver sus **cupones disponibles** y aplicarlos a sus pedidos.

### 5.1 Ver Mis Cupones

```
GET /api/campanias/cupones/mis-cupones
```

**Query params:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `vigentes` | bool | `true` | Solo cupones no usados y vigentes |

**Respuesta (200):**
```json
{
  "cupones": [
    {
      "id_campania_usuario": 1,
      "campania_id": 5,
      "nombre_campania": "Promo Navidad",
      "codigo": "NAVIDAD2025",
      "porcentaje_desc": 10.0,
      "fecha_vigencia": "2025-12-31T23:59:59",
      "usado": false
    },
    {
      "id_campania_usuario": 2,
      "campania_id": 8,
      "nombre_campania": "Cliente Frecuente",
      "codigo": "FRECUENTE15",
      "porcentaje_desc": 15.0,
      "fecha_vigencia": "2026-01-31T23:59:59",
      "usado": false
    }
  ],
  "total": 2
}
```

---

### 5.2 Ver Cupones de un Cliente Específico

```
GET /api/campanias/cupones/cliente/{cliente_id}
```

---

### 5.3 Validar Cupón

```
POST /api/campanias/cupones/validar
```

**Body:**
```json
{
  "codigo": "NAVIDAD2025",
  "cliente_id": 45
}
```

**Validaciones realizadas:**
1. ✅ Código de cupón existe
2. ✅ Campaña está activa
3. ✅ Cupón asignado al cliente
4. ✅ Cupón no usado previamente
5. ✅ Cupón dentro de fecha de vigencia (timezone México)

**Respuesta (200) - Cupón válido:**
```json
{
  "valido": true,
  "campania": {
    "id_campania": 5,
    "nombre_campania": "Promo Navidad"
  },
  "porcentaje_desc": 10.0,
  "campania_usuario_id": 1
}
```

**Respuesta (200) - Cupón inválido:**
```json
{
  "valido": false,
  "error": "Cupón ya fue utilizado"
}
```

---

### 5.4 Ver Campañas Activas

```
GET /api/campanias
```

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_campania": 5,
      "nombre": "Promo Navidad",
      "descripcion": "10% de descuento en todo",
      "porcentaje_desc": 10.0,
      "fecha_inicio": "2025-12-01T00:00:00",
      "fecha_fin": "2025-12-31T23:59:59",
      "es_activa": true
    }
  ]
}
```

---

### 5.5 Aplicar Cupón al Pago

El cupón se aplica al momento de **crear el pago**:

```
POST /api/pagos
```

**Body:**
```json
{
  "pedido_id": 100,
  "sucursal_id": 1,
  "monto": 500.00,
  "propina": 50.00,
  "moneda": "MXN",
  "campania_usuario_id": 1,
  "monto_descontado": 50.00
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `pedido_id` | int | ✅ | ID del pedido |
| `sucursal_id` | int | ✅ | ID de la sucursal |
| `monto` | float | ✅ | Monto antes de descuento |
| `propina` | float | ❌ | Propina (default: 0) |
| `moneda` | string | ❌ | Moneda (default: MXN) |
| `campania_usuario_id` | int | ❌ | ID del cupón a aplicar |
| `monto_descontado` | float | ❌ | Monto del descuento |

**Flujo:**
1. Validar cupón con `/api/campanias/cupones/validar`
2. Obtener `campania_usuario_id` de la respuesta
3. Enviar ese ID al crear el pago
4. El sistema aplica el descuento y marca el cupón como usado

---

## 6. Calificaciones y Mejoras

El cliente puede **calificar el servicio** y **enviar sugerencias** de mejora.

### 6.1 Crear Calificación

```
POST /api/calificaciones
```

**Body:**
```json
{
  "pedido_id": 100,
  "empleado_id": 5,
  "calificacion": 9,
  "notas": "Excelente servicio, muy amable y atento"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `pedido_id` | int | ✅ | ID del pedido |
| `empleado_id` | int | ❌ | ID del empleado calificado |
| `calificacion` | int | ✅ | Puntuación del 1 al 10 |
| `notas` | string | ❌ | Comentarios (max 300 chars) |

**Validaciones:**
- `calificacion`: Debe ser un entero entre 1 y 10
- `notas`: Máximo 300 caracteres
- No se puede calificar el mismo pedido dos veces

**Respuesta (201):**
```json
{
  "success": true,
  "data": {
    "id_calificacion": 1,
    "pedido_id": 100,
    "cliente_id": 45,
    "empleado_id": 5,
    "calificacion": 9,
    "notas": "Excelente servicio, muy amable y atento",
    "created_at": "2025-12-15T21:30:00"
  }
}
```

---

### 6.2 Ver Mis Calificaciones

```
GET /api/calificaciones
```

**Query params:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `pedido_id` | int | Filtrar por pedido |
| `empleado_id` | int | Filtrar por empleado |

> **Nota**: Los clientes solo ven sus propias calificaciones.

**Respuesta (200):**
```json
{
  "success": true,
  "data": [
    {
      "id_calificacion": 1,
      "pedido_id": 100,
      "empleado_id": 5,
      "calificacion": 9,
      "notas": "Excelente servicio",
      "created_at": "2025-12-15T21:30:00"
    }
  ]
}
```

---

### 6.3 Obtener Calificación por ID

```
GET /api/calificaciones/{calificacion_id}
```

---

### 6.4 Enviar Sugerencia de Mejora

```
POST /api/mejoras
```

**Body:**
```json
{
  "notas": "Sería bueno tener más opciones vegetarianas en el menú"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `notas` | string | ✅ | Sugerencia (1-300 caracteres) |

**Respuesta (201):**
```json
{
  "success": true,
  "data": {
    "id_mejora": 1,
    "cliente_id": 45,
    "notas": "Sería bueno tener más opciones vegetarianas en el menú",
    "estatus": 1,
    "created_at": "2025-12-15T21:35:00"
  }
}
```

---

### 6.5 Ver Mis Sugerencias

```
GET /api/mejoras
```

**Query params:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `estatus` | int | Filtrar por estado |

**Estados de Mejora:**
| Estado | Valor | Descripción |
|--------|-------|-------------|
| Registrada | `1` | Sugerencia recibida |
| En Proceso | `2` | Siendo evaluada |
| Implementada | `3` | Sugerencia aplicada |
| Descartada | `4` | No se implementará |

---

### 6.6 Obtener Sugerencia por ID

```
GET /api/mejoras/{mejora_id}
```

---

## 📱 Resumen de Endpoints para Cliente

### Catálogos
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/sucursales/activas` | 🔓 Ver sucursales |
| `GET` | `/api/areas?sucursal_id=X` | Ver áreas |
| `GET` | `/api/mesas?sucursal_id=X` | Ver mesas |

### Menú
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/categorias` | 🔓 Ver categorías |
| `GET` | `/api/productos` | 🔓 Ver productos |
| `GET` | `/api/combos` | 🔓 Ver combos |

### Reservas
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/holds/disponibilidad` | Verificar disponibilidad |
| `POST` | `/api/holds` | Crear hold |
| `POST` | `/api/holds/{id}/confirmar` | Confirmar hold |
| `POST` | `/api/holds/{id}/cancelar` | Cancelar hold |
| `POST` | `/api/reservas` | Crear reserva |
| `GET` | `/api/reservas/{id}` | Ver reserva |
| `POST` | `/api/reservas/listar` | Listar reservas |
| `POST` | `/api/reservas/{id}/cancelar` | Cancelar reserva |

### Pedidos
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/pedidos` | Crear Dine-in |
| `POST` | `/api/pedidos/para-llevar` | Crear Takeaway |
| `POST` | `/api/pedidos/{id}/items` | Agregar item |
| `GET` | `/api/pedidos/{id}` | Ver pedido |
| `POST` | `/api/pedidos/listar` | Listar pedidos |
| `PATCH` | `/api/pedidos/{id}/completar` | Completar pedido |
| `PATCH` | `/api/pedidos/{id}/cancelar` | Cancelar pedido |

### Cupones
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/campanias/cupones/mis-cupones` | Mis cupones |
| `POST` | `/api/campanias/cupones/validar` | Validar cupón |
| `GET` | `/api/campanias` | Ver campañas |
| `POST` | `/api/pagos` | Pagar con cupón |

### Calificaciones
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/calificaciones` | Calificar servicio |
| `GET` | `/api/calificaciones` | Mis calificaciones |
| `POST` | `/api/mejoras` | Enviar sugerencia |
| `GET` | `/api/mejoras` | Mis sugerencias |
