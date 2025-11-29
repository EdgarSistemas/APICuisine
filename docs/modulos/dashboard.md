# 📊 Dashboard Module

## Descripción
Módulo para visualización de métricas y KPIs en tiempo real del sistema de restaurante.
Proporciona datos para 25 gráficas distribuidas en 7 categorías.

---

## 🎯 KPIs Principales

### Obtener KPIs Dashboard Home
```
POST /api/dashboard/kpis
```

Retorna los indicadores clave para la vista principal:
- Ventas de hoy (total + transacciones)
- Pedidos activos
- Reservas de hoy
- Insumos bajo stock
- Lotes por vencer (próximos 7 días)
- Calificación promedio del mes

**Body:**
```json
{
  "sucursal_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ventas_hoy": {
      "total": 15000.00,
      "transacciones": 45
    },
    "pedidos_activos": 8,
    "reservas_hoy": 12,
    "insumos_bajo_stock": 3,
    "lotes_por_vencer": 5,
    "calificacion_promedio": 4.5,
    "fecha_consulta": "2025-01-15T14:30:00"
  }
}
```

---

## 💰 1. Ventas/Pagos (4 gráficas)

### 1.1 Ventas por Período
```
POST /api/dashboard/ventas/periodo
```

Ventas agrupadas por día, semana o mes para gráfica de línea/área.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59",
  "agrupar_por": "dia"  // dia | semana | mes
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"periodo": "2025-01-01", "cantidad": 25, "total": 12500.00, "propinas": 850.00},
    {"periodo": "2025-01-02", "cantidad": 30, "total": 15200.00, "propinas": 1100.00}
  ],
  "resumen": {
    "total_ventas": 27700.00,
    "total_propinas": 1950.00,
    "total_transacciones": 55,
    "ticket_promedio": 503.64
  }
}
```

---

### 1.2 Ventas por Sucursal
```
POST /api/dashboard/ventas/sucursales
```

Comparativa de ventas entre sucursales (solo admins ven todas).

**Body:**
```json
{
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"sucursal_id": 1, "sucursal_nombre": "Centro", "cantidad": 150, "total": 75000.00},
    {"sucursal_id": 2, "sucursal_nombre": "Norte", "cantidad": 120, "total": 60000.00}
  ]
}
```

---

### 1.3 Métodos de Pago
```
POST /api/dashboard/ventas/metodos-pago
```

Distribución de ventas por método de pago (pie/donut chart).

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"metodo_pago": 1, "metodo_nombre": "Efectivo", "cantidad": 80, "total": 35000.00},
    {"metodo_pago": 2, "metodo_nombre": "Tarjeta Débito", "cantidad": 50, "total": 25000.00},
    {"metodo_pago": 3, "metodo_nombre": "Tarjeta Crédito", "cantidad": 20, "total": 15000.00}
  ]
}
```

---

### 1.4 Propinas
Los totales de propinas están incluidos en el endpoint de **Ventas por Período** dentro del campo `propinas` por período y `total_propinas` en el resumen.

---

## 🍽️ 2. Pedidos (5 gráficas)

### 2.1 Pedidos por Estado
```
POST /api/dashboard/pedidos/estados
```

Distribución de pedidos por estado (pie/donut).

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"estado": 0, "estado_nombre": "Iniciado", "cantidad": 10},
    {"estado": 3, "estado_nombre": "Completo", "cantidad": 85},
    {"estado": 5, "estado_nombre": "Pagado", "cantidad": 150}
  ]
}
```

---

### 2.2 Dine-in vs Takeaway
```
POST /api/dashboard/pedidos/tipos
```

Comparativa entre pedidos en sitio y para llevar.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"tipo": 1, "tipo_nombre": "Dine-in", "cantidad": 200},
    {"tipo": 2, "tipo_nombre": "Takeaway", "cantidad": 45}
  ]
}
```

---

### 2.3 Pedidos por Hora
```
POST /api/dashboard/pedidos/horas
```

Distribución de pedidos por hora del día (barras).

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"hora": 12, "hora_display": "12:00", "cantidad": 45},
    {"hora": 13, "hora_display": "13:00", "cantidad": 60},
    {"hora": 14, "hora_display": "14:00", "cantidad": 55},
    {"hora": 19, "hora_display": "19:00", "cantidad": 40},
    {"hora": 20, "hora_display": "20:00", "cantidad": 50}
  ]
}
```

---

### 2.4 Top Productos
```
POST /api/dashboard/pedidos/top-productos
```

Los productos más vendidos (barras horizontales).

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59",
  "top_n": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"producto_id": 15, "producto_nombre": "Hamburguesa Clásica", "cantidad_total": 250, "veces_pedido": 200},
    {"producto_id": 8, "producto_nombre": "Tacos al Pastor", "cantidad_total": 180, "veces_pedido": 90}
  ]
}
```

---

### 2.5 Top Combos
```
POST /api/dashboard/pedidos/top-combos
```

Los combos más vendidos.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59",
  "top_n": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"combo_id": 3, "combo_nombre": "Combo Familiar", "cantidad_total": 85, "veces_pedido": 85},
    {"combo_id": 1, "combo_nombre": "Combo Individual", "cantidad_total": 120, "veces_pedido": 120}
  ]
}
```

---

## 📅 3. Reservas (3 gráficas)

### 3.1 Reservas por Estado
```
POST /api/dashboard/reservas/estados
```

Distribución de reservas por estado (pie/donut).

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"estado": 1, "estado_nombre": "Programada", "cantidad": 25},
    {"estado": 2, "estado_nombre": "En Curso", "cantidad": 5},
    {"estado": 3, "estado_nombre": "Completada", "cantidad": 180},
    {"estado": 4, "estado_nombre": "No Show", "cantidad": 12},
    {"estado": 5, "estado_nombre": "Cancelada", "cantidad": 8}
  ]
}
```

---

### 3.2 Tasa de Ocupación
La tasa de ocupación se puede calcular del lado del cliente usando:
- `Reservas por Estado` → Completadas vs Total
- `Endpoints de Mesas` → Mesas ocupadas vs Total

---

### 3.3 Tasa de No-Show
```
POST /api/dashboard/reservas/tasa-noshow
```

Porcentaje de clientes que no llegaron a su reserva.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_reservas": 197,
    "noshows": 12,
    "tasa_noshow": 6.09
  }
}
```

---

## 👥 4. CRM / Clientes (5 gráficas)

Para métricas de CRM, usar los endpoints existentes de Campañas:

### 4.1-4.5 Métricas CRM
```
POST /api/campanias/metricas
```

Incluye:
- Clientes VIP
- Clientes frecuentes
- Clientes inactivos
- Clientes nuevos
- Clientes por canal de contacto

Ver documentación completa en [Marketing Module](./marketing.md).

---

## 📦 5. Inventario (4 gráficas)

### 5.1 Insumos Bajo Stock
```
POST /api/dashboard/inventario/bajo-stock
```

Lista de insumos que están por debajo del stock mínimo.

**Body:**
```json
{
  "sucursal_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "insumo_id": 5,
      "insumo_nombre": "Carne de Res",
      "cantidad_actual": 8.5,
      "minimo_stock": 15.0,
      "faltante": 6.5
    },
    {
      "insumo_id": 12,
      "insumo_nombre": "Aceite Vegetal",
      "cantidad_actual": 2.0,
      "minimo_stock": 10.0,
      "faltante": 8.0
    }
  ],
  "total": 2
}
```

---

### 5.2 Lotes Próximos a Vencer
```
POST /api/dashboard/inventario/lotes-por-vencer
```

Lista de lotes que vencen próximamente con niveles de urgencia.

**Body:**
```json
{
  "sucursal_id": 1,
  "dias": 30
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "lote_id": 45,
      "insumo_nombre": "Queso Oaxaca",
      "lote": "L2025-001",
      "fecha_caducidad": "2025-01-20",
      "dias_para_vencer": 5,
      "cantidad_disponible": 15.5,
      "urgencia": "critico"
    }
  ],
  "resumen": {
    "total": 8,
    "criticos": 2,
    "altos": 3,
    "medios": 3
  }
}
```

**Niveles de Urgencia:**
- `critico`: <= 7 días
- `alto`: <= 14 días
- `medio`: > 14 días

---

### 5.3 Lotes Vencidos
```
POST /api/dashboard/inventario/lotes-vencidos
```

Lista de lotes que ya vencieron con cálculo de pérdida.

**Body:**
```json
{
  "sucursal_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "lote_id": 32,
      "insumo_nombre": "Leche Entera",
      "lote": "L2024-089",
      "fecha_caducidad": "2025-01-10",
      "cantidad_disponible": 5.0,
      "costo_total_perdida": 175.00
    }
  ],
  "resumen": {
    "total": 1,
    "perdida_total": 175.00
  }
}
```

---

### 5.4 Compras por Período
Usar el endpoint existente de compras:
```
POST /api/compras/listar
```

Ver documentación completa en [Almacén Module](./almacen.md).

---

## ⭐ 6. Calificaciones (2 gráficas)

### 6.1 Promedio de Calificaciones
```
POST /api/dashboard/calificaciones/promedio
```

Promedio general de calificaciones del servicio.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "promedio": 4.35,
    "total_calificaciones": 245,
    "calificacion_minima": 1,
    "calificacion_maxima": 5
  }
}
```

---

### 6.2 Top Empleados por Calificación
```
POST /api/dashboard/calificaciones/top-empleados
```

Los empleados mejor calificados.

**Body:**
```json
{
  "sucursal_id": 1,
  "fecha_desde": "2025-01-01T00:00:00",
  "fecha_hasta": "2025-01-31T23:59:59",
  "top_n": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"empleado_id": 15, "empleado_nombre": "María García", "promedio": 4.85, "total_calificaciones": 45},
    {"empleado_id": 8, "empleado_nombre": "Juan Pérez", "promedio": 4.72, "total_calificaciones": 38}
  ]
}
```

---

## 📋 7. Auditoría (2 gráficas)

Para métricas de auditoría, usar los endpoints existentes:

### 7.1 Acciones por Entidad
```
POST /api/auditoria/estadisticas
```

### 7.2 Acciones Frecuentes
```
POST /api/auditoria/estadisticas
```

Ver documentación completa en [Auditoría endpoints](../README.md).

---

## 📱 Resumen de Endpoints Dashboard

| # | Gráfica | Endpoint | Categoría |
|---|---------|----------|-----------|
| 1 | KPIs Principales | `POST /api/dashboard/kpis` | General |
| 2 | Ventas por Período | `POST /api/dashboard/ventas/periodo` | Ventas |
| 3 | Ventas por Sucursal | `POST /api/dashboard/ventas/sucursales` | Ventas |
| 4 | Métodos de Pago | `POST /api/dashboard/ventas/metodos-pago` | Ventas |
| 5 | Pedidos por Estado | `POST /api/dashboard/pedidos/estados` | Pedidos |
| 6 | Dine-in vs Takeaway | `POST /api/dashboard/pedidos/tipos` | Pedidos |
| 7 | Pedidos por Hora | `POST /api/dashboard/pedidos/horas` | Pedidos |
| 8 | Top Productos | `POST /api/dashboard/pedidos/top-productos` | Pedidos |
| 9 | Top Combos | `POST /api/dashboard/pedidos/top-combos` | Pedidos |
| 10 | Reservas por Estado | `POST /api/dashboard/reservas/estados` | Reservas |
| 11 | Tasa No-Show | `POST /api/dashboard/reservas/tasa-noshow` | Reservas |
| 12 | Insumos Bajo Stock | `POST /api/dashboard/inventario/bajo-stock` | Inventario |
| 13 | Lotes por Vencer | `POST /api/dashboard/inventario/lotes-por-vencer` | Inventario |
| 14 | Lotes Vencidos | `POST /api/dashboard/inventario/lotes-vencidos` | Inventario |
| 15 | Promedio Calificaciones | `POST /api/dashboard/calificaciones/promedio` | Calificaciones |
| 16 | Top Empleados | `POST /api/dashboard/calificaciones/top-empleados` | Calificaciones |

---

## 🔐 Autenticación

Todos los endpoints requieren JWT token en el header:
```
Authorization: Bearer <token>
```

El acceso a sucursales está controlado por el rol del usuario. Si no se envía `sucursal_id`, se usa la primera sucursal asignada al usuario.

---

## 📝 Notas de Implementación

1. **Fechas por defecto**: Si no se envían fechas, se usan los últimos 30 días.
2. **Zona horaria**: Todos los cálculos usan zona horaria de México (America/Mexico_City).
3. **Multi-tenant**: Todos los queries filtran por `sucursal_id` para garantizar aislamiento de datos.
4. **Cache**: Se recomienda implementar cache en el cliente para reducir llamadas al API.
