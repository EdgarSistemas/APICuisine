# GUÍA RÁPIDA - PRUEBAS HOLDMESA

## Paso 1: Arranca el servidor
```powershell
cd c:\Users\lenovo\Documents\cuisine\api\APICuisine
python app.py
```
Espera a ver: `Running on http://0.0.0.0:5000`

## Paso 2: Abre otra terminal PowerShell en el mismo directorio
```powershell
cd c:\Users\lenovo\Documents\cuisine\api\APICuisine
```

## Paso 3: Ejecuta las pruebas automáticas
```powershell
.\test_holdmesa.ps1
```

---

## PRUEBAS MANUALES (si prefieres via Swagger UI)

1. Abre en navegador: `http://localhost:5000/docs`
2. Haz click en "Authorize" (arriba a la derecha)
3. Ingresa el token (cópialo del login)
4. Prueba cada endpoint en orden:

### TEST 1: Crear Hold
- Endpoint: **POST /api/holds**
- Parámetro:
```json
{
  "mesa_id": 1,
  "actor_tipo": 2,
  "inicio": "2025-11-17T19:00:00",
  "fin_estimado": "2025-11-17T21:00:00",
  "ttl_minutes": 3,
  "notas": "Test hold"
}
```
- Respuesta esperada: Status 201, con `id_hold_mesa`

### TEST 2: Obtener Hold
- Endpoint: **GET /api/holds/{hold_id}**
- Reemplaza `{hold_id}` con el ID del hold creado (ej: 1)
- Respuesta esperada: Status 200, datos del hold

### TEST 3: Listar Holds
- Endpoint: **GET /api/holds**
- Respuesta esperada: Status 200, lista con el hold creado

### TEST 4: Verificar Disponibilidad
- Endpoint: **POST /api/holds/disponibilidad**
- Parámetro:
```json
{
  "mesa_id": 1,
  "inicio": "2025-11-17T19:00:00",
  "fin_estimado": "2025-11-17T21:00:00"
}
```
- Respuesta esperada: Status 200, `"disponible": false` (porque mesa 1 tiene hold)

### TEST 5: Cancelar Hold
- Endpoint: **POST /api/holds/{hold_id}/cancelar**
- Parámetro:
```json
{
  "motivo": "Test cancelación"
}
```
- Respuesta esperada: Status 200, hold con estatus 2

---

## PRUEBA DE EXPIRACIÓN (Manual)

1. Crea un hold (nota el `fechahora_expiracion`)
2. Espera 4 minutos
3. Intenta obtener el hold
4. Debe mostrar `"estatus": 3` (expirado)

El scheduler lo marca automáticamente cada minuto.

---

## PROBLEMAS COMUNES

### Error: "Sin autorización"
- Verifica que el token está en el header "Authorization"
- Formato correcto: `Bearer eyJhbGciOi...`

### Error: "Mesa no existe"
- Asegúrate que la mesa_id existe en la base de datos
- Intenta con mesa_id: 1, 2, 3, etc.

### Error: "Mesa no disponible"
- Ya existe un hold o reserva en ese rango de fechas
- Intenta con otra mesa o cambiar las horas

### El scheduler no marca expirados
- Verifica que está corriendo: `init_scheduler()` en app.py
- Revisa los logs del servidor para "HoldMesaScheduler"

---

## CHECKLIST FINAL

Después de todas las pruebas, verifica:

- [ ] HOLD creado sin errores
- [ ] HOLD obtenido correctamente
- [ ] HOLDS listados (mínimo 1)
- [ ] Disponibilidad verificada (false para mesa ocupada)
- [ ] HOLD cancelado
- [ ] RESERVA creada desde HOLD
- [ ] HOLD cambió a status 2 (usado)
- [ ] Disponibilidad de mesa liberada es true
- [ ] PEDIDO creado desde RESERVA
- [ ] Scheduler ejecutándose en logs

Si todo está ✓, el sistema está listo para las siguientes pruebas (inventario, pagos, etc.)

