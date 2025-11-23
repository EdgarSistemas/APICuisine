from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from src.core.config import get_config
from src.core.db.pool_manager import pool_manager
from src.core.swagger_config import init_swagger

# Importar blueprints
from src.controller.AuthController import auth_bp
from src.controller.UsuarioController import usuario_bp
from src.controller.RolController import roles_bp
from src.controller.AuditoriaController import auditoria_bp
from src.controller.SucursalesController import sucursales_bp
from src.controller.AreaController import bp as areas_bp
from src.controller.PedidoController import bp as pedidos_bp
from src.controller.CompraController import bp as compras_bp
from src.controller.MesaController import bp as mesas_bp
from src.controller.AsignacionMesaController import bp as asignaciones_mesa_bp
from src.controller.PagoController import bp as pagos_bp
from src.controller.UnidadMedidaController import bp as unidades_bp
from src.controller.InsumoController import bp as insumos_bp
from src.controller.CategoriaMenuController import bp as categorias_bp
from src.controller.ProductoController import bp as productos_bp
from src.controller.ComboController import bp as combos_bp
from src.controller.ProductoRecetaController import bp as recetas_bp
from src.controller.ProveedorController import bp as proveedores_bp
from src.controller.RecepcionController import bp as recepciones_bp
from src.controller.ConfigSucursalController import bp as config_bp
from src.controller.TicketController import bp as tickets_bp
from src.controller.CalificacionController import bp as calificaciones_bp
from src.controller.MejoraController import bp as mejoras_bp
from src.controller.HorarioController import horario_bp
from src.controller.UsuarioHorarioController import usuario_horario_bp
from src.controller.TurnoClaveController import turno_clave_bp
from src.controller.AsistenciaController import asistencia_bp
from src.controller.SolicitudVacacionesController import solicitud_vacaciones_bp
from src.controller.HoldMesaController import hold_mesa_bp
from src.controller.ReservaController import reserva_bp
from src.controller.MesaEstatusController import mesa_estatus_bp
from src.controller.JobsController import jobs_bp
from src.controller.PushNotificationController import bp as push_notifications_bp
 
def create_app():
  app = Flask(__name__)
  
  # Cargar configuración desde config.py
  config = get_config()
  app.config.from_object(config)
  
  # CORS simple y permisivo para desarrollo
  CORS(app, 
        origins="*",
        allow_headers="*",
        methods="*",
        supports_credentials=False
  )
  
  # Inicializar JWT Manager
  jwt = JWTManager(app)
  
  # Inicializar pool de conexiones
  pool_manager.initialize()
  
  # Inicializar Swagger con Flasgger
  init_swagger(app)

  # Registrar blueprints
  app.register_blueprint(auth_bp)
  app.register_blueprint(usuario_bp)
  app.register_blueprint(roles_bp)
  app.register_blueprint(auditoria_bp)
  app.register_blueprint(sucursales_bp)
  app.register_blueprint(areas_bp)
  app.register_blueprint(pedidos_bp)
  app.register_blueprint(compras_bp)
  app.register_blueprint(mesas_bp)
  app.register_blueprint(asignaciones_mesa_bp)
  app.register_blueprint(pagos_bp)
  app.register_blueprint(unidades_bp)
  app.register_blueprint(insumos_bp)
  app.register_blueprint(categorias_bp)
  app.register_blueprint(productos_bp)
  app.register_blueprint(combos_bp)
  app.register_blueprint(recetas_bp)
  app.register_blueprint(proveedores_bp)
  app.register_blueprint(recepciones_bp)
  app.register_blueprint(config_bp)
  app.register_blueprint(tickets_bp)
  app.register_blueprint(calificaciones_bp)
  app.register_blueprint(mejoras_bp)
  app.register_blueprint(horario_bp)
  app.register_blueprint(usuario_horario_bp)
  app.register_blueprint(turno_clave_bp)
  app.register_blueprint(asistencia_bp)
  app.register_blueprint(solicitud_vacaciones_bp)
  app.register_blueprint(hold_mesa_bp)
  app.register_blueprint(reserva_bp)
  app.register_blueprint(mesa_estatus_bp)
  app.register_blueprint(jobs_bp)
  app.register_blueprint(push_notifications_bp)

  # Manejo explícito de CORS para OPTIONS
  @app.before_request
  def handle_preflight():
      from flask import request
      if request.method == "OPTIONS":
          from flask import make_response
          response = make_response()
          response.headers.add("Access-Control-Allow-Origin", "*")
          response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
          response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS,PATCH")
          return response

  @app.route('/health')
  def health_check():
      """
      Estado de salud del sistema
      ---
      tags:
        - Sistema
      summary: Health check simple
      description: Endpoint básico para verificar que la API está funcionando
      responses:
        200:
          description: Sistema OK
          schema:
            type: object
            properties:
              status:
                type: string
                example: "OK"
              message:
                type: string
                example: "API funcionando"
      """
      return {"status": "OK", "message": "API funcionando"}, 200

  @app.route('/test-simple')
  def test_simple():
      """
      Test básico sin documentación compleja
      ---
      tags:
        - Sistema
      responses:
        200:
          description: Test OK
      """
      return {"test": "OK"}, 200

  @app.route('/')
  def index():
      return {
          "message": "Bienvenido a la API Cuisine",
          "version": "1.0.0",
          "documentation": {
              "swagger_ui": "/docs - Documentación Swagger UI interactiva",
              "swagger_json": "/apispec.json - Especificación OpenAPI JSON",
              "health": "/health - Estado del sistema"
          },
          "endpoints": {
              "auth": "/api/auth/* - Autenticación y tokens JWT",
              "usuarios": "/api/usuarios/* - Gestión de usuarios",
              "roles": "/api/roles/* - Gestión de roles y permisos",
              "auditoria": "/api/auditoria/* - Logs de auditoría y estadísticas",
              "catalogos": "/api/v1/catalogos/* - Catálogos: Sucursales, Areas, Mesas"
          }
      }, 200

  return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True,
        use_reloader=True
    )
