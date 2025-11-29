# Módulo: Almacén

> **Rol objetivo**: Personal de Compras/Almacén (rol ADMIN=1 o COMPRAS=8)  
> **Plataforma**: App Móvil

---

## 1. Registro de Compras

### Descripción
El personal de almacén puede registrar, consultar y cancelar compras desde la aplicación móvil. Registro básico **sin recepciones**.

---

### 1.1 Crear Compra

```
POST /api/compras
```

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "sucursal_id": 1,
  "proveedor_id": 5,
  "detalles": [
    {
      "insumo_id": 12,
      "cant_presentacion": 10.00,
      "costo_unit_present": 250.50,
      "presentacion": "costal 25kg"
    }
  ]
}
```

| Campo | Tipo | Requerido | Validación |
|-------|------|-----------|------------|
| sucursal_id | integer | ✅ | min: 1 |
| proveedor_id | integer | ✅ | min: 1 |
| detalles | array | ✅ | min: 1 item |
| detalles[].insumo_id | integer | ✅ | min: 1 |
| detalles[].cant_presentacion | decimal | ✅ | min: 0, 2 decimales |
| detalles[].costo_unit_present | decimal | ✅ | min: 0, 2 decimales |
| detalles[].presentacion | string | ✅ | 1-100 caracteres |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Compra 'COM-20251127143022' creada exitosamente con 1 artículos",
  "data": {
    "id_compra": 456,
    "usuario_id": 2,
    "sucursal_id": 1,
    "proveedor_id": 5,
    "folio": "COM-20251127143022",
    "fecha_compra": "2025-11-27 14:30:22",
    "estatus": 1,
    "created_at": "2025-11-27 14:30:22",
    "updated_at": null,
    "detalles": [
      {
        "id_compra_detalle": 789,
        "compra_id": 456,
        "insumo_id": 12,
        "cant_presentacion": 10.00,
        "costo_unit_present": 250.50,
        "created_at": "2025-11-27 14:30:22",
        "updated_at": null
      }
    ]
  }
}
```

**Errores posibles:**

| Código | Error | Causa |
|--------|-------|-------|
| 400 | VALIDATION_ERROR | Datos inválidos según schema |
| 400 | Sucursal {id} no existe | Sucursal inválida |
| 400 | Proveedor {id} no existe | Proveedor inválido |
| 400 | Insumo {id} no existe | Algún insumo no existe |
| 400 | Debe incluir al menos un detalle | Array vacío |
| 403 | Solo administradores o usuarios de compras... | Usuario sin permisos |

---

### 1.2 Listar Compras por Sucursal

```
GET /api/compras/{sucursal_id}
```

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| sucursal_id | integer | ID de la sucursal |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id_compra": 456,
      "usuario_id": 2,
      "sucursal_id": 1,
      "proveedor_id": 5,
      "folio": "COM-20251127143022",
      "fecha_compra": "2025-11-27 14:30:22",
      "estatus": 1,
      "created_at": "2025-11-27 14:30:22",
      "updated_at": null
    }
  ],
  "total": 1
}
```

---

### 1.3 Obtener Compra por ID (Detalle Completo)

```
GET /api/compras/id/{compra_id}
```

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| compra_id | integer | ID de la compra |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id_compra": 456,
    "folio": "COM-20251127143022",
    "fecha_compra": "2025-11-27 14:30:22",
    "estatus": 1,
    "total_compra": 2505.00,
    "created_at": "2025-11-27 14:30:22",
    "updated_at": null,
    "proveedor": {
      "id_proveedor": 5,
      "nombre": "Distribuidora El Sol",
      "telefono": "555-123-4567",
      "email": "ventas@elsol.com"
    },
    "sucursal": {
      "id_sucursal": 1,
      "nombre": "Sucursal Centro",
      "codigo_sucursal": "SUC001"
    },
    "usuario": {
      "id_usuario": 2,
      "nombre": "Juan",
      "apellido": "Pérez",
      "email": "juan@example.com"
    },
    "detalles": [
      {
        "id_compra_detalle": 789,
        "cant_presentacion": 10.00,
        "presentacion": "costal 25kg",
        "costo_unit_present": 250.50,
        "subtotal": 2505.00,
        "insumo": {
          "id_insumo": 12,
          "nombre": "Harina de Trigo",
          "unidad_medida": {
            "id_unidad_medida": 3,
            "clave": "KG",
            "nombre": "Kilogramo"
          }
        }
      }
    ]
  }
}
```

**Errores posibles:**

| Código | Error | Causa |
|--------|-------|-------|
| 404 | Compra {id} no encontrada | Compra no existe |

---

### 1.4 Cancelar Compra

```
PATCH /api/compras/id/{compra_id}/cancelar
```

**Headers:**
```
Authorization: Bearer {token}
```

**Path Parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| compra_id | integer | ID de la compra |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Compra 456 cancelada exitosamente"
}
```

**Errores posibles:**

| Código | Error | Causa |
|--------|-------|-------|
| 400 | La compra ya está cancelada | estatus = 3 |
| 400 | No se puede cancelar una compra que ya tiene recepción | estatus = 2 |
| 403 | Solo administradores o usuarios de compras... | Sin permisos |
| 404 | Compra {id} no existe | Compra inválida |

---

## 2. Estados de Compra

| Estatus | Nombre | Descripción |
|---------|--------|-------------|
| 1 | Registrada/Pendiente | Compra creada, sin recepción |
| 2 | Recibida | Tiene recepción asociada (no cancelable) |
| 3 | Cancelada | Compra cancelada |

---

## 3. Endpoints Externos Requeridos

### 3.1 Listar Proveedores

> **Controller**: `ProveedorController`

```
GET /api/proveedores
```

**Headers:**
```
(Sin autenticación requerida)
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id_proveedor": 5,
      "nombre": "Distribuidora El Sol",
      "telefono": "555-123-4567",
      "email": "ventas@elsol.com",
      "es_activo": true
    }
  ]
}
```

*Necesario para el selector de proveedor al crear compra.*

---

### 3.2 Listar Insumos con Existencias

> **Controller**: `InsumoController`

```
POST /api/insumos/existencias
```

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "sucursal_id": 1,
  "solo_activos": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id_insumo": 12,
      "nombre": "Harina de Trigo",
      "unidad_id": 3,
      "unidad_clave": "KG",
      "unidad_nombre": "Kilogramo",
      "es_activo": true,
      "cantidad": 50.00,
      "costo_promedio": 25.50,
      "updated_at": "2025-11-27 10:30:00"
    }
  ]
}
```

*Necesario para agregar items a la compra.*

---

### 3.3 Listar Insumos (sin existencias)

> **Controller**: `InsumoController`

```
GET /api/insumos
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id_insumo": 12,
      "nombre": "Harina de Trigo",
      "minimo_stock": 10.00,
      "unidad_id": 3,
      "es_activo": true
    }
  ]
}
```

*Alternativa si no se necesitan existencias.*

---

## 4. Validaciones del Backend

| Validación | Descripción |
|------------|-------------|
| Permisos | Solo rol `ADMIN` (1) o `COMPRAS` (8) |
| Sucursal | Debe existir |
| Proveedor | Debe existir |
| Detalles | Mínimo 1 detalle requerido |
| Insumos | Todos deben existir en catálogo |
| Cancelación | Solo compras en estatus 1 |

---

## 5. Flujo de Pantallas (App Móvil)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Lista Compras  │────>│  Nueva Compra   │────>│   Confirmación  │
│ GET /compras/   │     │                 │     │  POST /compras  │
│   {sucursal_id} │     │ 1. Proveedor    │     └─────────────────┘
└─────────────────┘     │ 2. + Insumos    │
        │               │ 3. Revisar      │
        ▼               └─────────────────┘
┌─────────────────┐
│ Detalle Compra  │
│ GET /compras/id/│
│   {compra_id}   │
│                 │
│ [Cancelar]      │──> PATCH .../cancelar
└─────────────────┘
```

---

## 6. Folio Automático

El sistema genera automáticamente el folio con formato:
```
COM-YYYYMMDDHHMMSS
```
Ejemplo: `COM-20251127143022`
