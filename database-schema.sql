-- DB CREATION
-- CREATE DATABASE db_cuisine;
-- USE db_cuisine;

-- USE master;
-- ALTER DATABASE db_cuisine SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
-- DROP DATABASE db_cuisine;

-- SCHEMAS
CREATE SCHEMA [catalogos];
GO
CREATE SCHEMA [operaciones];
GO
CREATE SCHEMA [seguridad];
GO
CREATE SCHEMA [inventario];
GO
CREATE SCHEMA [pagos];
GO
CREATE SCHEMA [config];
GO
CREATE SCHEMA [auditoria];
GO
CREATE SCHEMA [movil];
GO
CREATE SCHEMA [rrhh];
GO
CREATE SCHEMA [ticket];
GO
CREATE SCHEMA [servicio];
GO
CREATE SCHEMA [marketing];
GO

-- TABLES CREATION
CREATE TABLE [catalogos].[Sucursal] (
  [id_sucursal] INT PRIMARY KEY IDENTITY(1,1),
  [codigo_sucursal] NVARCHAR(20) UNIQUE NOT NULL,
  [nombre] NVARCHAR(100) NOT NULL,
  [telefono] NVARCHAR(15),
  [direccion] NVARCHAR(100),
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[Area] (
  [id_area] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT NOT NULL,
  [nombre] NVARCHAR(50) NOT NULL,
  [descripcion] NVARCHAR(100),
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [catalogos].[Mesa] (
  [id_mesa] INT PRIMARY KEY IDENTITY(1,1),
  [area_id] INT NOT NULL,
  [codigo_mesa] NVARCHAR(20) NOT NULL,
  [capacidad] INT NOT NULL,
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[MesaEstatus] (
  [id_mesa_estatus] INT PRIMARY KEY IDENTITY(1,1),
  [mesa_id] INT NOT NULL UNIQUE,
  [estatus] SMALLINT NOT NULL DEFAULT (1),
  [cambio_por] INT,
  [notas] NVARCHAR(200),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[CategoriaMenu] (
  [id_categoria] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(30) NOT NULL,
  [descripcion] NVARCHAR(100),
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[Producto] (
  [id_producto] INT PRIMARY KEY IDENTITY(1,1),
  [categoria_id] INT NOT NULL,
  [codigo] NVARCHAR(20),
  [nombre] NVARCHAR(50) NOT NULL,
  [descripcion] NVARCHAR(100),
  [imagen_url] NVARCHAR(MAX),
  [precio] DECIMAL(12,2) NOT NULL,
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[Combo] (
  [id_combo] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(50) NOT NULL,
  [descripcion] NVARCHAR(100),
  [imagen_url] NVARCHAR(MAX),
  [precio] DECIMAL(12,2) NOT NULL,
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[ComboProducto] (
  [id_combo_producto] INT PRIMARY KEY IDENTITY(1,1),
  [combo_id] INT NOT NULL,
  [producto_id] INT NOT NULL,
  [cantidad] INT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[ProductoReceta] (
  [id_receta] INT PRIMARY KEY IDENTITY(1,1),
  [producto_id] INT NOT NULL,
  [nombre] NVARCHAR(120),
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [catalogos].[ProductoRecetaItem] (
  [id_receta_item] INT PRIMARY KEY IDENTITY(1,1),
  [receta_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [cantidad] DECIMAL(10,2) NOT NULL
);
GO

CREATE TABLE [operaciones].[AsignacionMesa] (
  [id_asignacion_mesa] INT PRIMARY KEY IDENTITY(1,1),
  [mesa_id] INT NOT NULL,
  [usuario_id] INT NOT NULL,
  [es_activa] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [operaciones].[Pedido] (
  [id_pedido] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT NOT NULL,
  [folio] NVARCHAR(20) NOT NULL,
  [cliente_id] INT,
  [tipo_pedido] TINYINT NOT NULL,
  [canal] TINYINT NOT NULL,
  [reserva_id] INT,
  [mesa_id] INT,
  [inicia_usuario_id] INT NOT NULL,
  [estado_pedido] TINYINT NOT NULL,
  [notas] NVARCHAR(100),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [operaciones].[PedidoItem] (
  [id_pedido_item] INT PRIMARY KEY IDENTITY(1,1),
  [pedido_id] INT NOT NULL,
  [producto_id] INT NULL,
  [combo_id] INT NULL,
  [cantidad] INT NOT NULL DEFAULT (1),
  [precio_unit] DECIMAL(12,2) NOT NULL,
  [notas] NVARCHAR(100),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2,
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [operaciones].[PedidoEstadoHist] (
  [id_pedido_estado_hist] INT PRIMARY KEY IDENTITY(1,1),
  [pedido_id] INT NOT NULL,
  [estado_pedido] TINYINT NOT NULL,
  [usuario_id] INT,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [comentario] NVARCHAR(100)
);
GO

CREATE TABLE [operaciones].[HoldMesa] (
  [id_hold_mesa] INT PRIMARY KEY IDENTITY(1,1),
  [mesa_id] INT NOT NULL,
  [actor_tipo] TINYINT NOT NULL,
  [actor_usuario_id] INT,
  [inicio] DATETIME2 NOT NULL,
  [fin_estimado] DATETIME2 NOT NULL,
  [expires_at] DATETIME2 NOT NULL,
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [notas] NVARCHAR(300),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2,
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [operaciones].[Reserva] (
  [id_reserva] INT PRIMARY KEY IDENTITY(1,1),
  [cliente_id] INT,
  [recepcionista_id] INT,
  [inicio] DATETIME2 NOT NULL,
  [fin_estimado] DATETIME2 NOT NULL,
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [tolerancia_min] INT,
  [notas] NVARCHAR(300),
  [hold_id] INT,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2,
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [seguridad].[Rol] (
  [id_rol] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(30) UNIQUE NOT NULL,
  [descripcion] NVARCHAR(100)
);
GO

CREATE TABLE [seguridad].[Usuario] (
  [id_usuario] [int] IDENTITY(1,1) NOT NULL,
	[email] [nvarchar](50) NOT NULL,
	[hash_password] [nvarchar](max) NULL,
	[nombre] [nvarchar](50) NOT NULL,
	[apellido] [nvarchar](30) NULL,
	[telefono] [nvarchar](30) NULL,
	[es_activo] [bit] NOT NULL,
	[es_cliente] [bit] NOT NULL,
	[acepta_marketing] [bit] NOT NULL,
	[tipo_acceso] [nvarchar](5) NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NULL,
);
GO

CREATE TABLE [seguridad].[UsuarioRol] (
  [id_usuario_rol] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [rol_id] INT NOT NULL
);
GO

CREATE TABLE [seguridad].[UsuarioSucursal] (
  [id_usuario_sucursal] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [sucursal_id] INT NOT NULL
);
GO

CREATE TABLE [seguridad].[Modulo] (
  [id_modulo] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(30) NOT NULL,
  [clave] NVARCHAR(20) UNIQUE NOT NULL,
  [descripcion] NVARCHAR(100),
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [seguridad].[RolModulo] (
  [id_rol_modulo] INT PRIMARY KEY IDENTITY(1,1),
  [rol_id] INT NOT NULL,
  [modulo_id] INT NOT NULL,
  [habilitado] BIT NOT NULL DEFAULT (1),
  [plataforma] TINYINT
);
GO

CREATE TABLE [inventario].[UnidadMedida] (
  [id_unidad] INT PRIMARY KEY IDENTITY(1,1),
  [clave] NVARCHAR(20) UNIQUE NOT NULL,
  [nombre] NVARCHAR(30) NOT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [inventario].[Insumo] (
  [id_insumo] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(30) NOT NULL,
  [unidad_id] INT NOT NULL,
  [es_activo] BIT NOT NULL DEFAULT (1),
  [minimo_stock] DECIMAL(10,2) NOT NULL DEFAULT (0),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [inventario].[Existencia] (
  [id_existencia] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [cantidad] DECIMAL(10,2) NOT NULL DEFAULT (0),
  [costo_promedio] DECIMAL(10,2) NOT NULL DEFAULT (0),
  [updated_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [inventario].[Proveedor] (
  [id_proveedor] INT PRIMARY KEY IDENTITY(1,1),
  [nombre] NVARCHAR(30) NOT NULL,
  [telefono] NVARCHAR(15),
  [email] NVARCHAR(50),
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [inventario].[Compra] (
  [id_compra] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [sucursal_id] INT NOT NULL,
  [proveedor_id] INT NOT NULL,
  [folio] NVARCHAR(20) NOT NULL,
  [fecha_compra] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [inventario].[CompraDetalle] (
  [id_compra_detalle] INT PRIMARY KEY IDENTITY(1,1),
  [compra_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [cant_presentacion] DECIMAL(10,2) NOT NULL,
  [costo_unit_present] DECIMAL(10,2) NOT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [inventario].[Recepcion] (
  [id_recepcion] INT PRIMARY KEY IDENTITY(1,1),
  [compra_id] INT,
  [recibido_por] INT,
  [fecha_recepcion] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [notas] NVARCHAR(200),
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [inventario].[RecepcionDetalle] (
  [id_recepcion_det] INT PRIMARY KEY IDENTITY(1,1),
  [recepcion_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [cant_presentacion] DECIMAL(10,2) NOT NULL,
  [unidades_por_present] DECIMAL(10,2) NOT NULL,
  [cantidad_base] DECIMAL(10,2) NOT NULL,
  [costo_unitario] DECIMAL(10,2) NOT NULL,
  [notas] NVARCHAR(200),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [inventario].[Lote] (
  [id_lote] INT PRIMARY KEY IDENTITY(1,1),
  [det_recepcion_id] INT NOT NULL,
  [lote] NVARCHAR(20),
  [lote_proveedor] NVARCHAR(100),
  [cantidad_inicial] DECIMAL(10,2) NOT NULL,
  [cantidad_disponible] DECIMAL(10,2) NOT NULL,
  [costo_unitario] DECIMAL(10,2) NOT NULL,
  [fecha_caducidad] DATETIME2,
  [estado] TINYINT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [inventario].[Movimiento] (
  [id_movimiento] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [lote_id] INT,
  [tipo_mov] TINYINT NOT NULL,
  [motivo] TINYINT NOT NULL,
  [cantidad] DECIMAL(10,2) NOT NULL,
  [pedido_id] INT,
  [det_recepcion_id] INT,
  [compra_id] INT,
  [merma_id] INT,
  [usuario_id] INT,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [inventario].[Merma] (
  [id_merma] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT NOT NULL,
  [insumo_id] INT NOT NULL,
  [cantidad] DECIMAL(10,2) NOT NULL,
  [motivo] NVARCHAR(200),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [pagos].[Pago] (
  [id_pago] INT PRIMARY KEY IDENTITY(1,1),
  [pedido_id] INT NOT NULL,
  [sucursal_id] INT NOT NULL,
  [monto] DECIMAL(10,2) NOT NULL,
  [propina] DECIMAL(10,2) NOT NULL DEFAULT (0),
  [moneda] NVARCHAR(5) NOT NULL DEFAULT ('MXN'),
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [usuario_id] INT,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [config].[ConfigSucursal] (
  [id_config] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT,
  [clave] NVARCHAR(30) NOT NULL,
  [valor_string] NVARCHAR(300),
  [updated_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [rowversion] ROWVERSION
);
GO

CREATE TABLE [auditoria].[LogAccion] (
  [id_log_accion] INT PRIMARY KEY IDENTITY(1,1),
  [origen] NVARCHAR(40) NOT NULL,
  [entidad] NVARCHAR(120) NOT NULL,
  [entidad_id] NVARCHAR(80),
  [accion] NVARCHAR(40) NOT NULL,
  [usuario_id] INT,
  [detalle_json] NVARCHAR(MAX),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [movil].[PushToken] (
  [id_push_token] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT,
  [plataforma] NVARCHAR(10) NOT NULL,
  [token] NVARCHAR(255) UNIQUE NOT NULL,
  [es_activo] BIT NOT NULL DEFAULT (1),
  [creado_en] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [actualizado_en] DATETIME2
);
GO

CREATE TABLE [rrhh].[Horario] (
  [id_horario] INT PRIMARY KEY IDENTITY(1,1),
  [sucursal_id] INT,
  [clave] NVARCHAR(60) UNIQUE NOT NULL,
  [nombre] NVARCHAR(120) NOT NULL,
  [descripcion] NVARCHAR(300),
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [rrhh].[HorarioDetalle] (
  [id_detalle] INT PRIMARY KEY IDENTITY(1,1),
  [horario_id] INT NOT NULL,
  [dia_semana] TINYINT NOT NULL,
  [hora_inicio] TIME NOT NULL,
  [hora_fin] TIME NOT NULL,
  [turno_idx] TINYINT NOT NULL DEFAULT (1),
  [tolerancia_min] INT NOT NULL DEFAULT (10),
  [es_activo] BIT NOT NULL DEFAULT (1)
);
GO

CREATE TABLE [rrhh].[UsuarioHorario] (
  [id_usuario_horario] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [horario_id] INT NOT NULL,
  [fecha_inicio] DATE NOT NULL,
  [fecha_fin] DATE,
  [es_recurring] BIT NOT NULL DEFAULT (1),
  [es_activo] BIT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [updated_at] DATETIME2
);
GO

CREATE TABLE [rrhh].[SolicitudVacaciones] (
  [id_solicitud] INT PRIMARY KEY IDENTITY(1,1),
  [horario_usuario_id] INT NOT NULL,
  [fecha_inicio] DATE NOT NULL,
  [fecha_fin] DATE NOT NULL,
  [motivo] NVARCHAR(300),
  [estatus] TINYINT DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [rrhh].[TurnoClave] (
  [id_turno_clave] INT PRIMARY KEY IDENTITY(1,1),
  [horario_id] INT NOT NULL,
  [horario_detalle_id] INT,
  [sucursal_id] INT NOT NULL,
  [fecha] DATE NOT NULL,
  [turno_idx] TINYINT NOT NULL DEFAULT (1),
  [codigo] NVARCHAR(32) NOT NULL,
  [hash_codigo] NVARCHAR(128),
  [es_activo] BIT NOT NULL DEFAULT (1),
  [generado_por] INT,
  [generado_en] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [expira_en] DATETIME2,
  [uso_maximo] INT NOT NULL DEFAULT (0),
  [usos_count] INT NOT NULL DEFAULT (0),
  [notas] NVARCHAR(300)
);
GO

CREATE TABLE [rrhh].[Asistencia] (
  [id_asistencia] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [usuario_horario_id] INT,
  [tipo_evento] TINYINT NOT NULL,
  [evento_ts] DATETIME2 NOT NULL,
  [origen] NVARCHAR(20),
  [device_info] NVARCHAR(300),
  [lat] DECIMAL(9,6),
  [lng] DECIMAL(9,6),
  [turno_clave_id] INT,
  [codigo_usuario] NVARCHAR(32),
  [codigo_validado] BIT NOT NULL DEFAULT (0),
  [observaciones] NVARCHAR(300),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [ticket].[Ticket] (
  [id_ticket] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_id] INT NOT NULL,
  [notas] NVARCHAR(500),
  [imagen_url] NVARCHAR(MAX),
  [estatus] TINYINT NOT NULL DEFAULT (1),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE [servicio].[Calificacion] (
  [id_calificacion] INT PRIMARY KEY IDENTITY(1,1),
  [pedido_id] INT NOT NULL,
  [cliente_id] INT NOT NULL,
  [empleado_id] INT NOT NULL,
  [notas] NVARCHAR(300),
  [calificacion] TINYINT NOT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [es_activo] TINYINT NOT NULL DEFAULT (1)
);
GO

CREATE TABLE [servicio].[Mejoras] (
  [id_mejora] INT PRIMARY KEY IDENTITY(1,1),
  [cliente_id] INT NOT NULL,
  [notas] NVARCHAR(300),
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [estatus] TINYINT NOT NULL DEFAULT (1)
);
GO

CREATE TABLE [marketing].[Campania] (
  [id_campania] INT PRIMARY KEY IDENTITY(1,1),
  [usuario_crea_id] INT NOT NULL,
  [nombre_campania] NVARCHAR(100) NOT NULL,
  [porcentaje_desc] DECIMAL(10,2) NOT NULL,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME()),
  [estatus] TINYINT NOT NULL DEFAULT (1)
);
GO

CREATE TABLE [marketing].[CampaniaUsuario] (
  [id_campania_usuario] INT PRIMARY KEY IDENTITY(1,1),
  [cliente_id] INT NOT NULL,
  [campania_id] INT NOT NULL,
  [fecha_vigencia] DATETIME2,
  [created_at] DATETIME2 NOT NULL DEFAULT (SYSUTCDATETIME())
);
GO

-- INDEX CREATION
-- CREATE UNIQUE INDEX [UQ_Mesa_Sucursal_Codigo] ON [catalogos].[Mesa] ([sucursal_id], [codigo_mesa]);
-- GO

-- CREATE INDEX [IX_Mesa_SucursalArea] ON [catalogos].[Mesa] ([sucursal_id], [area_id]);
-- GO

CREATE UNIQUE INDEX [UQ_Producto_SKU] ON [catalogos].[Producto] ([codigo]);
GO

CREATE INDEX [IX_Menu_CategoriaActivoNombre] ON [catalogos].[Producto] ([categoria_id], [es_activo], [nombre]);
GO

CREATE UNIQUE INDEX [UX_Combo_Producto_Unico] ON [catalogos].[ComboProducto] ([combo_id], [producto_id]);
GO

CREATE INDEX [IX_ComboProducto_PorProducto] ON [catalogos].[ComboProducto] ([producto_id]);
GO

CREATE INDEX [IX_Receta_PorProductoActiva] ON [catalogos].[ProductoReceta] ([producto_id], [es_activa]);
GO

CREATE UNIQUE INDEX [UX_Receta_Insumo] ON [catalogos].[ProductoRecetaItem] ([receta_id], [insumo_id]);
GO

CREATE UNIQUE INDEX [UX_AsigMesa_MesaUsuarioActiva] ON [operaciones].[AsignacionMesa] ([mesa_id], [usuario_id], [es_activa]);
GO

CREATE INDEX [IX_AsigMesa_MesaActiva] ON [operaciones].[AsignacionMesa] ([mesa_id], [es_activa]);
GO

CREATE INDEX [IX_AsigMesa_MeseroActivo] ON [operaciones].[AsignacionMesa] ([usuario_id], [es_activa]);
GO

CREATE UNIQUE INDEX [UQ_Pedido_Folio_Sucursal] ON [operaciones].[Pedido] ([sucursal_id], [folio]);
GO

CREATE INDEX [IX_Pedido_SucursalFecha] ON [operaciones].[Pedido] ([sucursal_id], [created_at]);
GO

CREATE INDEX [IX_Pedido_Estado] ON [operaciones].[Pedido] ([estado_pedido]);
GO

CREATE INDEX [IX_Pedido_MesaEstado] ON [operaciones].[Pedido] ([sucursal_id], [mesa_id], [estado_pedido]);
GO

CREATE INDEX [IX_PedidoItem_Pedido] ON [operaciones].[PedidoItem] ([pedido_id]);
GO

CREATE INDEX [IX_HoldMesa_Expira] ON [operaciones].[HoldMesa] ([mesa_id], [expires_at]);
GO

CREATE INDEX [IX_HoldMesa_Estatus] ON [operaciones].[HoldMesa] ([mesa_id], [estatus]);
GO

CREATE INDEX [IX_Reserva_MesaRango] ON [operaciones].[Reserva] ([inicio], [fin_estimado]);
GO

CREATE INDEX [IX_Reserva_Busqueda] ON [operaciones].[Reserva] ([estatus], [inicio]);
GO

CREATE UNIQUE INDEX [UX_Reserva_Hold_Unico] ON [operaciones].[Reserva] ([hold_id]);
GO

CREATE UNIQUE INDEX [UX_Usuario_Rol] ON [seguridad].[UsuarioRol] ([usuario_id], [rol_id]);
GO

CREATE UNIQUE INDEX [UX_Usuario_Sucursal] ON [seguridad].[UsuarioSucursal] ([usuario_id], [sucursal_id]);
GO

CREATE UNIQUE INDEX [UX_Rol_Modulo] ON [seguridad].[RolModulo] ([rol_id], [modulo_id]);
GO

CREATE UNIQUE INDEX [UX_Existencia_SucursalInsumo] ON [inventario].[Existencia] ([sucursal_id], [insumo_id]);
GO

CREATE UNIQUE INDEX [UX_Compra_Folio_Sucursal] ON [inventario].[Compra] ([sucursal_id], [folio]);
GO

CREATE INDEX [IX_Mov_Pedido] ON [inventario].[Movimiento] ([pedido_id]);
GO

CREATE INDEX [IX_Mov_det_recepcion_id] ON [inventario].[Movimiento] ([det_recepcion_id]);
GO

CREATE INDEX [IX_Pago_Pedido] ON [pagos].[Pago] ([pedido_id]);
GO

CREATE INDEX [IX_Pago_PedidoEstatus] ON [pagos].[Pago] ([pedido_id], [estatus]);
GO

CREATE INDEX [IX_Pago_SucursalFecha] ON [pagos].[Pago] ([sucursal_id], [created_at]);
GO

CREATE UNIQUE INDEX [UX_ConfigSucursal_SucursalClave] ON [config].[ConfigSucursal] ([sucursal_id], [clave]);
GO

CREATE INDEX [IX_LogAccion_Fecha] ON [auditoria].[LogAccion] ([created_at]);
GO

CREATE INDEX [IX_LogAccion_UsuarioFecha] ON [auditoria].[LogAccion] ([usuario_id], [created_at]);
GO

CREATE INDEX [IX_LogAccion_EntidadAccionFecha] ON [auditoria].[LogAccion] ([entidad], [accion], [created_at]);
GO

CREATE INDEX [IX_PushToken_Usuario] ON [movil].[PushToken] ([usuario_id], [es_activo]);
GO

CREATE INDEX [IX_PushToken_Plataforma] ON [movil].[PushToken] ([plataforma], [es_activo]);
GO

CREATE UNIQUE INDEX [UX_HorarioDetalle_Unico] ON [rrhh].[HorarioDetalle] ([horario_id], [dia_semana], [turno_idx]);
GO

CREATE INDEX [IX_UsuarioHorario_Activo] ON [rrhh].[UsuarioHorario] ([usuario_id], [es_activo]);
GO

CREATE UNIQUE INDEX [UX_TurnoClave_HorarioFechaTurno] ON [rrhh].[TurnoClave] ([horario_id], [fecha], [turno_idx]);
GO

CREATE INDEX [IX_TurnoClave_SucursalFecha] ON [rrhh].[TurnoClave] ([sucursal_id], [fecha]);
GO

CREATE INDEX [IX_TurnoClave_Codigo] ON [rrhh].[TurnoClave] ([codigo]);
GO

CREATE INDEX [IX_Asistencia_UsuarioFecha] ON [rrhh].[Asistencia] ([usuario_id], [evento_ts]);
GO

CREATE INDEX [IX_Asistencia_SucursalFecha] ON [rrhh].[Asistencia] ([evento_ts]);
GO

CREATE INDEX [IX_Asistencia_TurnoClave] ON [rrhh].[Asistencia] ([turno_clave_id]);
GO

-- CONSTRAINT CREATION
-- catalogos.Area.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [catalogos].[Area]
  ADD CONSTRAINT FK_Area_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- catalogos.Mesa.area_id -> catalogos.Area.id_area
ALTER TABLE [catalogos].[Mesa]
  ADD CONSTRAINT FK_Mesa_Area FOREIGN KEY ([area_id]) REFERENCES [catalogos].[Area]([id_area]);
GO

-- catalogos.MesaEstatus.mesa_id -> catalogos.Mesa.id_mesa
ALTER TABLE [catalogos].[MesaEstatus]
  ADD CONSTRAINT FK_MesaEstatus_Mesa FOREIGN KEY ([mesa_id]) REFERENCES [catalogos].[Mesa]([id_mesa]);
GO

-- catalogos.MesaEstatus.cambio_por -> seguridad.Usuario.id_usuario
ALTER TABLE [catalogos].[MesaEstatus]
  ADD CONSTRAINT FK_MesaEstatus_UsuarioCambio FOREIGN KEY ([cambio_por]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- catalogos.Mesa.sucursal_id -> catalogos.Sucursal.id_sucursal
-- ALTER TABLE [catalogos].[Mesa]
--  ADD CONSTRAINT FK_Mesa_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
-- GO

-- operaciones.AsignacionMesa.mesa_id -> catalogos.Mesa.id_mesa
ALTER TABLE [operaciones].[AsignacionMesa]
  ADD CONSTRAINT FK_AsignacionMesa_Mesa FOREIGN KEY ([mesa_id]) REFERENCES [catalogos].[Mesa]([id_mesa]);
GO

-- operaciones.AsignacionMesa.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[AsignacionMesa]
  ADD CONSTRAINT FK_AsignacionMesa_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- catalogos.Producto.categoria_id -> catalogos.CategoriaMenu.id_categoria
ALTER TABLE [catalogos].[Producto]
  ADD CONSTRAINT FK_Producto_Categoria FOREIGN KEY ([categoria_id]) REFERENCES [catalogos].[CategoriaMenu]([id_categoria]);
GO

-- catalogos.ComboProducto.combo_id -> catalogos.Combo.id_combo
ALTER TABLE [catalogos].[ComboProducto]
  ADD CONSTRAINT FK_ComboProducto_Combo FOREIGN KEY ([combo_id]) REFERENCES [catalogos].[Combo]([id_combo]);
GO

-- catalogos.ComboProducto.producto_id -> catalogos.Producto.id_producto
ALTER TABLE [catalogos].[ComboProducto]
  ADD CONSTRAINT FK_ComboProducto_Producto FOREIGN KEY ([producto_id]) REFERENCES [catalogos].[Producto]([id_producto]);
GO

-- catalogos.ProductoReceta.producto_id -> catalogos.Producto.id_producto
ALTER TABLE [catalogos].[ProductoReceta]
  ADD CONSTRAINT FK_ProductoReceta_Producto FOREIGN KEY ([producto_id]) REFERENCES [catalogos].[Producto]([id_producto]);
GO

-- catalogos.ProductoRecetaItem.receta_id -> catalogos.ProductoReceta.id_receta
ALTER TABLE [catalogos].[ProductoRecetaItem]
  ADD CONSTRAINT FK_ProductoRecetaItem_Receta FOREIGN KEY ([receta_id]) REFERENCES [catalogos].[ProductoReceta]([id_receta]);
GO

-- catalogos.ProductoRecetaItem.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [catalogos].[ProductoRecetaItem]
  ADD CONSTRAINT FK_ProductoRecetaItem_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- seguridad.UsuarioRol.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [seguridad].[UsuarioRol]
  ADD CONSTRAINT FK_UsuarioRol_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- seguridad.UsuarioRol.rol_id -> seguridad.Rol.id_rol
ALTER TABLE [seguridad].[UsuarioRol]
  ADD CONSTRAINT FK_UsuarioRol_Rol FOREIGN KEY ([rol_id]) REFERENCES [seguridad].[Rol]([id_rol]);
GO

-- seguridad.UsuarioSucursal.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [seguridad].[UsuarioSucursal]
  ADD CONSTRAINT FK_UsuarioSucursal_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- seguridad.UsuarioSucursal.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [seguridad].[UsuarioSucursal]
  ADD CONSTRAINT FK_UsuarioSucursal_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- seguridad.RolModulo.rol_id -> seguridad.Rol.id_rol
ALTER TABLE [seguridad].[RolModulo]
  ADD CONSTRAINT FK_RolModulo_Rol FOREIGN KEY ([rol_id]) REFERENCES [seguridad].[Rol]([id_rol]);
GO

-- seguridad.RolModulo.modulo_id -> seguridad.Modulo.id_modulo
ALTER TABLE [seguridad].[RolModulo]
  ADD CONSTRAINT FK_RolModulo_Modulo FOREIGN KEY ([modulo_id]) REFERENCES [seguridad].[Modulo]([id_modulo]);
GO

-- operaciones.Pedido.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [operaciones].[Pedido]
  ADD CONSTRAINT FK_Pedido_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- operaciones.Pedido.cliente_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[Pedido]
  ADD CONSTRAINT FK_Pedido_Cliente FOREIGN KEY ([cliente_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.Pedido.inicia_usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[Pedido]
  ADD CONSTRAINT FK_Pedido_IniciaUsuario FOREIGN KEY ([inicia_usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.Pedido.mesa_id -> catalogos.Mesa.id_mesa
ALTER TABLE [operaciones].[Pedido]
  ADD CONSTRAINT FK_Pedido_Mesa FOREIGN KEY ([mesa_id]) REFERENCES [catalogos].[Mesa]([id_mesa]);
GO

-- operaciones.PedidoItem.pedido_id -> operaciones.Pedido.id_pedido
ALTER TABLE [operaciones].[PedidoItem]
  ADD CONSTRAINT FK_PedidoItem_Pedido FOREIGN KEY ([pedido_id]) REFERENCES [operaciones].[Pedido]([id_pedido]);
GO

-- operaciones.PedidoItem.producto_id -> catalogos.Producto.id_producto
ALTER TABLE [operaciones].[PedidoItem]
  ADD CONSTRAINT FK_PedidoItem_Producto FOREIGN KEY ([producto_id]) REFERENCES [catalogos].[Producto]([id_producto]);
GO

-- operaciones.PedidoItem.combo_id -> catalogos.Combo.id_combo
ALTER TABLE [operaciones].[PedidoItem]
  ADD CONSTRAINT FK_PedidoItem_Combo FOREIGN KEY ([combo_id]) REFERENCES [catalogos].[Combo]([id_combo]);
GO

-- operaciones.PedidoEstadoHist.pedido_id -> operaciones.Pedido.id_pedido
ALTER TABLE [operaciones].[PedidoEstadoHist]
  ADD CONSTRAINT FK_PedidoEstadoHist_Pedido FOREIGN KEY ([pedido_id]) REFERENCES [operaciones].[Pedido]([id_pedido]);
GO

-- operaciones.PedidoEstadoHist.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[PedidoEstadoHist]
  ADD CONSTRAINT FK_PedidoEstadoHist_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- inventario.Insumo.unidad_id -> inventario.UnidadMedida.id_unidad
ALTER TABLE [inventario].[Insumo]
  ADD CONSTRAINT FK_Insumo_Unidad FOREIGN KEY ([unidad_id]) REFERENCES [inventario].[UnidadMedida]([id_unidad]);
GO

-- inventario.Existencia.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [inventario].[Existencia]
  ADD CONSTRAINT FK_Existencia_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- inventario.Existencia.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [inventario].[Existencia]
  ADD CONSTRAINT FK_Existencia_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- inventario.Compra.proveedor_id -> inventario.Proveedor.id_proveedor
ALTER TABLE [inventario].[Compra]
  ADD CONSTRAINT FK_Compra_Proveedor FOREIGN KEY ([proveedor_id]) REFERENCES [inventario].[Proveedor]([id_proveedor]);
GO

-- inventario.Compra.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [inventario].[Compra]
  ADD CONSTRAINT FK_Compra_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- inventario.Compra.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [inventario].[Compra]
  ADD CONSTRAINT FK_Compra_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- inventario.CompraDetalle.compra_id -> inventario.Compra.id_compra
ALTER TABLE [inventario].[CompraDetalle]
  ADD CONSTRAINT FK_CompraDetalle_Compra FOREIGN KEY ([compra_id]) REFERENCES [inventario].[Compra]([id_compra]);
GO

-- inventario.CompraDetalle.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [inventario].[CompraDetalle]
  ADD CONSTRAINT FK_CompraDetalle_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- inventario.Recepcion.compra_id -> inventario.Compra.id_compra
ALTER TABLE [inventario].[Recepcion]
  ADD CONSTRAINT FK_Recepcion_Compra FOREIGN KEY ([compra_id]) REFERENCES [inventario].[Compra]([id_compra]);
GO

-- inventario.Recepcion.recibido_por -> seguridad.Usuario.id_usuario
ALTER TABLE [inventario].[Recepcion]
  ADD CONSTRAINT FK_Recepcion_RecibidoPor FOREIGN KEY ([recibido_por]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- inventario.RecepcionDetalle.recepcion_id -> inventario.Recepcion.id_recepcion
ALTER TABLE [inventario].[RecepcionDetalle]
  ADD CONSTRAINT FK_RecepcionDetalle_Recepcion FOREIGN KEY ([recepcion_id]) REFERENCES [inventario].[Recepcion]([id_recepcion]);
GO

-- inventario.RecepcionDetalle.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [inventario].[RecepcionDetalle]
  ADD CONSTRAINT FK_RecepcionDetalle_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- inventario.Lote.det_recepcion_id -> inventario.RecepcionDetalle.id_recepcion_det
ALTER TABLE [inventario].[Lote]
  ADD CONSTRAINT FK_Lote_RecepcionDetalle FOREIGN KEY ([det_recepcion_id]) REFERENCES [inventario].[RecepcionDetalle]([id_recepcion_det]);
GO

ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);

ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_RecepcionDetalle FOREIGN KEY ([det_recepcion_id]) REFERENCES [inventario].[RecepcionDetalle]([id_recepcion_det]);

-- inventario.Movimiento.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- inventario.Movimiento.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- inventario.Movimiento.lote_id -> inventario.Lote.id_lote
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Lote FOREIGN KEY ([lote_id]) REFERENCES [inventario].[Lote]([id_lote]);
GO

-- inventario.Movimiento.pedido_id -> operaciones.Pedido.id_pedido
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Pedido FOREIGN KEY ([pedido_id]) REFERENCES [operaciones].[Pedido]([id_pedido]);
GO

-- inventario.Movimiento.compra_id -> inventario.Compra.id_compra
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Compra FOREIGN KEY ([compra_id]) REFERENCES [inventario].[Compra]([id_compra]);
GO

-- inventario.Movimiento.merma_id -> inventario.Merma.id_merma
ALTER TABLE [inventario].[Movimiento]
  ADD CONSTRAINT FK_Movimiento_Merma FOREIGN KEY ([merma_id]) REFERENCES [inventario].[Merma]([id_merma]);
GO

-- inventario.Merma.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [inventario].[Merma]
  ADD CONSTRAINT FK_Merma_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- inventario.Merma.insumo_id -> inventario.Insumo.id_insumo
ALTER TABLE [inventario].[Merma]
  ADD CONSTRAINT FK_Merma_Insumo FOREIGN KEY ([insumo_id]) REFERENCES [inventario].[Insumo]([id_insumo]);
GO

-- pagos.Pago.pedido_id -> operaciones.Pedido.id_pedido
ALTER TABLE [pagos].[Pago]
  ADD CONSTRAINT FK_Pago_Pedido FOREIGN KEY ([pedido_id]) REFERENCES [operaciones].[Pedido]([id_pedido]);
GO

-- pagos.Pago.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [pagos].[Pago]
  ADD CONSTRAINT FK_Pago_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- pagos.Pago.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [pagos].[Pago]
  ADD CONSTRAINT FK_Pago_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.HoldMesa.mesa_id -> catalogos.Mesa.id_mesa
ALTER TABLE [operaciones].[HoldMesa]
  ADD CONSTRAINT FK_HoldMesa_Mesa FOREIGN KEY ([mesa_id]) REFERENCES [catalogos].[Mesa]([id_mesa]);
GO

-- operaciones.HoldMesa.actor_usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[HoldMesa]
  ADD CONSTRAINT FK_HoldMesa_ActorUsuario FOREIGN KEY ([actor_usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.Reserva.cliente_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[Reserva]
  ADD CONSTRAINT FK_Reserva_Cliente FOREIGN KEY ([cliente_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.Reserva.recepcionista_id -> seguridad.Usuario.id_usuario
ALTER TABLE [operaciones].[Reserva]
  ADD CONSTRAINT FK_Reserva_Recepcionista FOREIGN KEY ([recepcionista_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- operaciones.Reserva.hold_id -> operaciones.HoldMesa.id_hold_mesa
ALTER TABLE [operaciones].[Reserva]
  ADD CONSTRAINT FK_Reserva_Hold FOREIGN KEY ([hold_id]) REFERENCES [operaciones].[HoldMesa]([id_hold_mesa]);
GO

-- config.ConfigSucursal.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [config].[ConfigSucursal]
  ADD CONSTRAINT FK_ConfigSucursal_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- auditoria.LogAccion.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [auditoria].[LogAccion]
  ADD CONSTRAINT FK_LogAccion_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- movil.PushToken.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [movil].[PushToken]
  ADD CONSTRAINT FK_PushToken_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- rrhh.Horario.sucursal_id -> catalogos.Sucursal.id_sucursal
ALTER TABLE [rrhh].[Horario]
  ADD CONSTRAINT FK_Horario_Sucursal FOREIGN KEY ([sucursal_id]) REFERENCES [catalogos].[Sucursal]([id_sucursal]);
GO

-- rrhh.HorarioDetalle.horario_id -> rrhh.Horario.id_horario
ALTER TABLE [rrhh].[HorarioDetalle]
  ADD CONSTRAINT FK_HorarioDetalle_Horario FOREIGN KEY ([horario_id]) REFERENCES [rrhh].[Horario]([id_horario]);
GO

-- rrhh.UsuarioHorario.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [rrhh].[UsuarioHorario]
  ADD CONSTRAINT FK_UsuarioHorario_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- rrhh.UsuarioHorario.horario_id -> rrhh.Horario.id_horario
ALTER TABLE [rrhh].[UsuarioHorario]
  ADD CONSTRAINT FK_UsuarioHorario_Horario FOREIGN KEY ([horario_id]) REFERENCES [rrhh].[Horario]([id_horario]);
GO

-- rrhh.TurnoClave.horario_detalle_id -> rrhh.HorarioDetalle.id_detalle
ALTER TABLE [rrhh].[TurnoClave]
  ADD CONSTRAINT FK_TurnoClave_HorarioDetalle FOREIGN KEY ([horario_detalle_id]) REFERENCES [rrhh].[HorarioDetalle]([id_detalle]);
GO

-- rrhh.TurnoClave.generado_por -> seguridad.Usuario.id_usuario
ALTER TABLE [rrhh].[TurnoClave]
  ADD CONSTRAINT FK_TurnoClave_GeneradoPor FOREIGN KEY ([generado_por]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- rrhh.Asistencia.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [rrhh].[Asistencia]
  ADD CONSTRAINT FK_Asistencia_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- rrhh.Asistencia.usuario_horario_id -> rrhh.UsuarioHorario.id_usuario_horario
ALTER TABLE [rrhh].[Asistencia]
  ADD CONSTRAINT FK_Asistencia_UsuarioHorario FOREIGN KEY ([usuario_horario_id]) REFERENCES [rrhh].[UsuarioHorario]([id_usuario_horario]);
GO

-- rrhh.Asistencia.turno_clave_id -> rrhh.TurnoClave.id_turno_clave
ALTER TABLE [rrhh].[Asistencia]
  ADD CONSTRAINT FK_Asistencia_TurnoClave FOREIGN KEY ([turno_clave_id]) REFERENCES [rrhh].[TurnoClave]([id_turno_clave]);
GO

-- rrhh.SolicitudVacaciones.horario_usuario_id -> rrhh.UsuarioHorario.id_usuario_horario
ALTER TABLE [rrhh].[SolicitudVacaciones]
  ADD CONSTRAINT FK_SolicitudVacaciones_UsuarioHorario FOREIGN KEY ([horario_usuario_id]) REFERENCES [rrhh].[UsuarioHorario]([id_usuario_horario]);
GO

-- ticket.Ticket.usuario_id -> seguridad.Usuario.id_usuario
ALTER TABLE [ticket].[Ticket]
  ADD CONSTRAINT FK_Ticket_Usuario FOREIGN KEY ([usuario_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- servicio.Calificacion.pedido_id -> operaciones.Pedido.id_pedido
ALTER TABLE [servicio].[Calificacion]
  ADD CONSTRAINT FK_Calificacion_Pedido FOREIGN KEY ([pedido_id]) REFERENCES [operaciones].[Pedido]([id_pedido]);
GO

-- servicio.Calificacion.cliente_id -> seguridad.Usuario.id_usuario
ALTER TABLE [servicio].[Calificacion]
  ADD CONSTRAINT FK_Calificacion_Cliente FOREIGN KEY ([cliente_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

ALTER TABLE [servicio].[Calificacion]
  ADD CONSTRAINT FK_Calificacion_Empleado FOREIGN KEY ([empleado_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);

-- servicio.Mejoras.cliente_id -> seguridad.Usuario.id_usuario
ALTER TABLE [servicio].[Mejoras]
  ADD CONSTRAINT FK_Mejoras_Cliente FOREIGN KEY ([cliente_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- marketing.Campania.usuario_crea_id -> seguridad.Usuario.id_usuario
ALTER TABLE [marketing].[Campania]
  ADD CONSTRAINT FK_Campania_UsuarioCrea FOREIGN KEY ([usuario_crea_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO

-- marketing.CampaniaUsuario.campania_id -> marketing.Campania.id_campania
ALTER TABLE [marketing].[CampaniaUsuario]
  ADD CONSTRAINT FK_CampaniaUsuario_Campania FOREIGN KEY ([campania_id]) REFERENCES [marketing].[Campania]([id_campania]);
GO

-- marketing.CampaniaUsuario.cliente_id -> seguridad.Usuario.id_usuario
ALTER TABLE [marketing].[CampaniaUsuario]
  ADD CONSTRAINT FK_CampaniaUsuario_Cliente FOREIGN KEY ([cliente_id]) REFERENCES [seguridad].[Usuario]([id_usuario]);
GO