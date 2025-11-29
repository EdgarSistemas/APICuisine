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
6. [Calificaciones](#6-calificaciones)

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
| Disponible | 1 | Mesa libre para reservar |
| Ocupada | 2 | Mesa en uso |
| En Limpieza | 3 | Mesa siendo preparada |
| Fuera de Servicio | 4 | Mesa no disponible |

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

El cliente **elige la sucursal y mesa**, luego crea su reserva usando el sistema de Hold.

### 3.1 Sistema de Hold

Antes de crear una reserva, se debe **bloquear la mesa** por 3 minutos.

#### Crear Hold en Mesa

```
POST /api/holds
```

**Body:**
```json
{
  "mesa_id": 5,
  "inicio": "2025-06-15 19:00:00",
  "fin": "2025-06-15 21:00:00"
}
```

**Respuesta (201):**
```json
{
  "mensaje": "Hold creado exitosamente",
  "hold": {
    "id_hold": 123,
    "mesa_id": 5,
    "expira_at": "2025-06-15T18:03:00",
    "ttl_segundos": 180
  }
}
```

> ⏱️ **TTL de 3 minutos**: Si no se crea la reserva, el hold expira automáticamente.

#### Cancelar Hold

```
DELETE /api/holds/{hold_id}
```

---

### 3.2 Crear Reserva

```
POST /api/reservas
```

**Body:**
```json
{
  "cliente_id": 45,
  "hold_id": 123,
  "inicio": "2025-06-15 19:00:00",
  "fin_estimado": "2025-06-15 21:00:00",
  "tolerancia_min": 15,
  "notas": "Cumpleaños, mesa cerca de ventana"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `cliente_id` | int | ✅ | ID del cliente (del JWT) |
| `hold_id` | int | ✅ | ID del hold activo |
| `inicio` | string | ✅ | Fecha/hora `yyyy-mm-dd hh:mm:ss` |
| `fin_estimado` | string | ✅ | Fecha/hora fin estimada |
| `tolerancia_min` | int | ❌ | Minutos de tolerancia (default: 15) |
| `notas` | string | ❌ | Notas adicionales |

**Respuesta (201):**
```json
{
  "mensaje": "Reserva creada exitosamente",
  "reserva": {
    "id_reserva": 789,
    "mesa_id": 5,
    "cliente_id": 45,
    "inicio": "2025-06-15T19:00:00",
    "fin_estimado": "2025-06-15T21:00:00",
    "estado": 0,
    "tolerancia_min": 15
  }
}
```

---

### 3.3 Consultar Reserva

```
GET /api/reservas/{reserva_id}
```

---

### 3.4 Listar Mis Reservas

```
POST /api/reservas/listar
```

**Body:**
```json
{
  "cliente_id": 45,
  "estado": 0,
  "fecha_desde": "2025-06-01",
  "fecha_hasta": "2025-06-30"
}
```

---

### 3.5 Cancelar Reserva

```
POST /api/reservas/{reserva_id}/cancelar
```

**Body (opcional):**
```json
{
  "motivo": "Cambio de planes"
}
```

---

### 3.6 Estados de Reserva

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Confirmada | 0 | Reserva activa, esperando cliente |
| Iniciada | 1 | Cliente llegó, mesa ocupada |
| Completada | 2 | Servicio finalizado |
| Cancelada | 3 | Cancelada por cliente o sistema |
| No-Show | 4 | Cliente no llegó |

---

## 4. Pedidos

El cliente puede hacer **su propio pedido** tanto en sitio como para llevar.

### 4.1 Crear Pedido Dine-in (En sitio)

```
POST /api/pedidos
```

Para consumo en el restaurante. **Requiere reserva activa**.

**Body:**
```json
{
  "sucursal_id": 1,
  "cliente_id": 45,
  "reserva_id": 789,
  "items": [
    {
      "producto_id": 10,
      "cantidad": 2,
      "notas": "Sin cebolla"
    },
    {
      "combo_id": 5,
      "cantidad": 1
    }
  ],
  "canal": "App",
  "notas": "Mesa junto a ventana"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `sucursal_id` | int | ✅ | ID de sucursal |
| `cliente_id` | int | ✅ | ID del cliente |
| `reserva_id` | int | ✅ | ID de reserva activa |
| `items` | array | ✅ | Al menos 1 item |
| `items[].producto_id` | int | XOR | Producto (excluyente con combo_id) |
| `items[].combo_id` | int | XOR | Combo (excluyente con producto_id) |
| `items[].cantidad` | int | ✅ | Cantidad |
| `items[].notas` | string | ❌ | Notas del item |

**Respuesta (201):**
```json
{
  "mensaje": "Pedido creado - Items en cocina",
  "pedido": {
    "id_pedido": 1234,
    "tipo_pedido": 1,
    "estado": 0,
    "items_creados": 3,
    "total_estimado": 450.00
  }
}
```

---

### 4.2 Crear Pedido Para Llevar (Takeaway)

```
POST /api/pedidos/para-llevar
```

Para comida para llevar. **No requiere reserva**.

**Body:**
```json
{
  "sucursal_id": 1,
  "cliente_id": 45,
  "items": [
    {
      "producto_id": 15,
      "cantidad": 1
    },
    {
      "combo_id": 3,
      "cantidad": 2,
      "notas": "Sin picante"
    }
  ],
  "canal": "App",
  "notas": "Recoger en 30 min"
}
```

**Respuesta (201):**
```json
{
  "mensaje": "Pedido para llevar creado - En cocina",
  "pedido": {
    "id_pedido": 1235,
    "tipo_pedido": 2,
    "estado": 0,
    "items_creados": 3
  }
}
```

> 💰 **Auto-pago**: Cuando cocina marca todos los items como `Listo`, el pedido cambia automáticamente a `Pagado`.

---

### 4.3 Agregar Item a Pedido

```
POST /api/pedidos/{pedido_id}/items
```

**Body:**
```json
{
  "producto_id": 12,
  "cantidad": 1,
  "notas": "Extra queso"
}
```

---

### 4.4 Consultar Pedido

```
GET /api/pedidos/{pedido_id}
```

**Respuesta:**
```json
{
  "pedido": {
    "id_pedido": 1234,
    "tipo_pedido": 1,
    "tipo_descripcion": "Dine-in",
    "estado": 0,
    "estado_descripcion": "Iniciado",
    "items": [
      {
        "id_item": 567,
        "producto": "Hamburguesa Clásica",
        "cantidad": 2,
        "estado": 1,
        "estado_descripcion": "En Cocina"
      }
    ],
    "total": 450.00
  }
}
```

---

### 4.5 Completar Pedido

```
PATCH /api/pedidos/{pedido_id}/completar
```

---

### 4.6 Cancelar Pedido

```
PATCH /api/pedidos/{pedido_id}/cancelar
```

---

### 4.7 Listar Mis Pedidos

```
POST /api/pedidos/listar
```

**Body:**
```json
{
  "sucursal_id": 1,
  "cliente_id": 45,
  "estado": 0,
  "tipo_pedido": 2
}
```

---

### 4.8 Estados de Pedido

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Iniciado | 0 | Pedido creado, items en cocina |
| Completo | 3 | Cliente cerró el pedido |
| Cancelado | 4 | Pedido cancelado |
| Pagado | 5 | Pago completado |

### 4.9 Estados de Item

| Estado | Valor | Descripción |
|--------|-------|-------------|
| Pendiente | 0 | En cola |
| En Cocina | 1 | Cocinándose |
| Listo | 2 | Listo para servir |
| Entregado | 3 | Entregado al cliente |
| Cancelado | 4 | Item cancelado |

---

## 5. CRM - Cupones

El cliente puede ver y usar sus cupones disponibles.

### 5.1 Mis Cupones

```
GET /api/campanias/cupones/mis-cupones
```

**Query params:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `solo_disponibles` | bool | true | Solo cupones no usados y vigentes |

**Respuesta:**
```json
{
  "cupones": [
    {
      "id": 45,
      "codigo": "NAVIDAD2025",
      "campania": "Promoción Navidad",
      "porcentaje_desc": 15.00,
      "fecha_expira": "2025-12-31",
      "estatus": 0,
      "estatus_descripcion": "Disponible"
    }
  ],
  "total": 1
}
```

---

### 5.2 Validar Cupón

```
POST /api/campanias/cupones/validar
```

Valida si un cupón es aplicable antes de usarlo en el pago.

**Body:**
```json
{
  "codigo": "NAVIDAD2025",
  "cliente_id": 45
}
```

**Respuesta:**
```json
{
  "valido": true,
  "campania": {
    "nombre": "Promoción Navidad",
    "descripcion": "15% de descuento"
  },
  "porcentaje_desc": 15.00,
  "campania_usuario_id": 123
}
```

---

### 5.3 Estados de Cupón

| Estado | Valor | Descripción |
|--------|-------|-------------|
| No Usado | 0 | Disponible para usar |
| Usado | 1 | Ya fue aplicado |
| Vencido | 2 | Expiró sin usarse |

---

## 6. Calificaciones

El cliente puede calificar el servicio **después de que el pedido esté pagado**.

> ⚠️ **Requisito**: El pedido debe estar en estado `Pagado (5)` para poder calificar.

### 6.1 Crear Calificación

```
POST /api/calificaciones
```

**Body:**
```json
{
  "pedido_id": 1234,
  "empleado_id": 78,
  "calificacion": 9,
  "notas": "Excelente atención, muy amable"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `pedido_id` | int | ✅ | ID del pedido (debe estar pagado) |
| `empleado_id` | int | ✅ | ID del mesero/empleado |
| `calificacion` | int | ✅ | Puntuación de **1 a 10** |
| `notas` | string | ❌ | Comentarios |

**Respuesta (201):**
```json
{
  "mensaje": "Calificación registrada",
  "calificacion": {
    "id_calificacion": 456,
    "pedido_id": 1234,
    "empleado_id": 78,
    "calificacion": 9,
    "notas": "Excelente atención"
  }
}
```

---

### 6.2 Listar Mis Calificaciones

```
GET /api/calificaciones?pedido_id={id}
```

---

## 📊 Resumen de Endpoints

### Catálogos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/sucursales/activas` | Listar sucursales (público) |
| GET | `/api/sucursales/{id}` | Obtener sucursal |
| GET | `/api/areas?sucursal_id={id}` | Listar áreas |
| GET | `/api/mesas?sucursal_id={id}` | Listar mesas |

### Menú
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/categorias` | Listar categorías (público) |
| GET | `/api/productos` | Listar productos (público) |
| GET | `/api/productos/{id}` | Obtener producto |
| GET | `/api/combos` | Listar combos (público) |
| GET | `/api/combos/{id}` | Obtener combo |

### Reservas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/holds` | Crear hold (3 min) |
| DELETE | `/api/holds/{id}` | Cancelar hold |
| POST | `/api/reservas` | Crear reserva |
| GET | `/api/reservas/{id}` | Consultar reserva |
| POST | `/api/reservas/listar` | Listar reservas |
| POST | `/api/reservas/{id}/cancelar` | Cancelar reserva |

### Pedidos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/pedidos` | Crear pedido dine-in |
| POST | `/api/pedidos/para-llevar` | Crear pedido takeaway |
| GET | `/api/pedidos/{id}` | Consultar pedido |
| POST | `/api/pedidos/{id}/items` | Agregar item |
| PATCH | `/api/pedidos/{id}/completar` | Completar pedido |
| PATCH | `/api/pedidos/{id}/cancelar` | Cancelar pedido |
| POST | `/api/pedidos/listar` | Listar pedidos |

### Cupones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/campanias/cupones/mis-cupones` | Mis cupones |
| POST | `/api/campanias/cupones/validar` | Validar cupón |

### Calificaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/calificaciones` | Crear calificación |
| GET | `/api/calificaciones` | Listar calificaciones |

---

## 🔄 Flujos Típicos

### Reserva + Pedido Dine-in
```
1. GET /api/sucursales/activas   → Elegir sucursal
2. GET /api/areas?sucursal_id=1  → Ver áreas
3. GET /api/mesas?sucursal_id=1  → Elegir mesa disponible
4. POST /api/holds               → Bloquear mesa (3 min)
5. POST /api/reservas            → Crear reserva
6. [Cliente llega al restaurante]
7. GET /api/categorias           → Ver menú
8. GET /api/productos            → Ver productos
9. GET /api/combos               → Ver combos
10. POST /api/pedidos            → Crear pedido con items
11. [Esperar cocina]
12. [Pagar en caja]
13. POST /api/calificaciones     → Calificar servicio
```

### Pedido Para Llevar
```
1. GET /api/sucursales/activas   → Elegir sucursal
2. GET /api/categorias           → Ver menú
3. GET /api/productos            → Ver productos
4. GET /api/combos               → Ver combos
5. POST /api/pedidos/para-llevar → Crear pedido
6. [Esperar notificación "Listo"]
7. [Recoger - Auto-pagado]
```

### Usar Cupón
```
1. GET /api/campanias/cupones/mis-cupones → Ver cupones
2. POST /api/campanias/cupones/validar    → Validar cupón
3. [Aplicar descuento en pago]
```
