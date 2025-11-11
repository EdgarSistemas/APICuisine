"""
Servicio de email para envío de códigos de verificación
"""

import smtplib
import logging
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from src.core.config import get_config

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de emails con códigos de verificación"""
    
    def __init__(self):
        self.config = get_config()
    
    def generar_codigo(self, length: int = 6) -> str:
        """
        Genera un código aleatorio de dígitos
        
        Args:
            length: Longitud del código (default: 6)
            
        Returns:
            Código numérico como string
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def enviar_codigo_reset(self, email: str, codigo: str, nombre: str = "") -> Dict[str, Any]:
        """
        Envía código de verificación para reset de contraseña
        
        Args:
            email: Email destino
            codigo: Código de verificación
            nombre: Nombre del usuario (opcional)
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # Si está en modo debug, solo imprimir
            if self.config.EMAIL_DEBUG:
                logger.info(f"[EMAIL DEBUG] Código de reset para {email}: {codigo}")
                return {
                    'success': True,
                    'message': f'Código enviado a {email}',
                    'debug': True,
                    'codigo': codigo  # Solo para debug
                }
            
            # Crear el mensaje
            subject = "Código de verificación - Sistema Cuisine"
            body = self._crear_template_reset(codigo, nombre)
            
            # Enviar email
            resultado = self._enviar_email(email, subject, body)
            
            if resultado['success']:
                logger.info(f"Código de reset enviado exitosamente a {email}")
                return {
                    'success': True,
                    'message': f'Código enviado a {email}'
                }
            else:
                logger.error(f"Error al enviar código a {email}: {resultado['error']}")
                return {
                    'success': False,
                    'message': 'Error al enviar código',
                    'error': resultado['error']
                }
            
        except Exception as e:
            logger.error(f"Error en enviar_codigo_reset: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno al enviar código',
                'error': str(e)
            }
    
    def _crear_template_reset(self, codigo: str, nombre: str = "") -> str:
        """
        Crea el template HTML para email de reset de contraseña
        
        Args:
            codigo: Código de verificación
            nombre: Nombre del usuario
            
        Returns:
            HTML del email
        """
        saludo = f"Hola {nombre}," if nombre else "Hola,"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Sistema Cuisine</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p>{saludo}</p>
                    <p>Has solicitado restablecer tu contraseña. Usa el siguiente código de verificación:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #e74c3c; letter-spacing: 5px; background-color: #fff; padding: 15px 25px; border: 2px dashed #e74c3c; border-radius: 5px; display: inline-block;">
                            {codigo}
                        </span>
                    </div>
                    
                    <p><strong>Este código expira en 15 minutos.</strong></p>
                    <p>Si no solicitaste este cambio, ignora este email.</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #666; text-align: center;">
                    Este es un email automático, no responder.<br>
                    Sistema Cuisine © 2025
                </p>
            </div>
        </body>
        </html>
        """
    
    def _enviar_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Envía email usando SMTP
        
        Args:
            to_email: Email destino
            subject: Asunto del email
            body: Cuerpo del email (HTML)
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.SMTP_FROM_NAME} <{self.config.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar cuerpo HTML
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Conectar y enviar
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                server.send_message(msg)
            
            return {'success': True}
            
        except smtplib.SMTPAuthenticationError as e:
            return {
                'success': False,
                'error': f'Error de autenticación SMTP: {str(e)}'
            }
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'error': f'Error SMTP: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error general: {str(e)}'
            }
    
    def validar_configuracion(self) -> Dict[str, Any]:
        """
        Valida que la configuración SMTP esté completa
        
        Returns:
            Dict con estado de la validación
        """
        errores = []
        
        if not self.config.SMTP_USERNAME:
            errores.append("SMTP_USERNAME no configurado")
        
        if not self.config.SMTP_PASSWORD:
            errores.append("SMTP_PASSWORD no configurado")
        
        if not self.config.SMTP_FROM_EMAIL:
            errores.append("SMTP_FROM_EMAIL no configurado")
        
        return {
            'valida': len(errores) == 0,
            'errores': errores,
            'debug_mode': self.config.EMAIL_DEBUG
        }