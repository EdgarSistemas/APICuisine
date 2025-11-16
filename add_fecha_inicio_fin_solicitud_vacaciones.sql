-- =============================================
-- Migración: Agregar fecha_inicio y fecha_fin a SolicitudVacaciones
-- Fecha: 2025-11-14
-- Descripción: Agrega los campos fecha_inicio y fecha_fin a la tabla rrhh.SolicitudVacaciones
-- =============================================

USE [db_cuisine];
GO

-- Verificar si las columnas ya existen antes de agregarlas
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('rrhh.SolicitudVacaciones') 
    AND name = 'fecha_inicio'
)
BEGIN
    ALTER TABLE [rrhh].[SolicitudVacaciones]
    ADD [fecha_inicio] DATE NOT NULL DEFAULT '2025-01-01';
    
    PRINT 'Columna fecha_inicio agregada exitosamente';
END
ELSE
BEGIN
    PRINT 'Columna fecha_inicio ya existe';
END
GO

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('rrhh.SolicitudVacaciones') 
    AND name = 'fecha_fin'
)
BEGIN
    ALTER TABLE [rrhh].[SolicitudVacaciones]
    ADD [fecha_fin] DATE NOT NULL DEFAULT '2025-01-01';
    
    PRINT 'Columna fecha_fin agregada exitosamente';
END
ELSE
BEGIN
    PRINT 'Columna fecha_fin ya existe';
END
GO

-- Opcional: Eliminar valores por defecto temporales
-- (Solo si prefieres que no tengan DEFAULT en producción)
/*
ALTER TABLE [rrhh].[SolicitudVacaciones]
DROP CONSTRAINT IF EXISTS DF__SolicitudVacaciones__fecha_inicio;

ALTER TABLE [rrhh].[SolicitudVacaciones]
DROP CONSTRAINT IF EXISTS DF__SolicitudVacaciones__fecha_fin;
*/

PRINT 'Migración completada exitosamente';
GO
