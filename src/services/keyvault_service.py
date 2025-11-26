"""
KeyVaultService - Servicio para obtener secretos desde Azure Key Vault

Uso:
    keyvault = KeyVaultService()
    secret = keyvault.get_secret("mi-secreto")
    json_secret = keyvault.get_secret_as_json("firebase-credentials")
"""

import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Cargar variables de entorno desde .env
load_dotenv()

logger = logging.getLogger(__name__)


class KeyVaultService:
    """
    Servicio para interactuar con Azure Key Vault.
    
    Autenticación:
        - En Azure (App Service, VM, AKS): Usa Managed Identity automáticamente
        - En local: Usa Azure CLI (az login) o variables de entorno
        
    Variables de entorno opcionales para desarrollo local:
        AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
    """
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Inicializa el cliente de Key Vault.
        
        Args:
            vault_url: URL del Key Vault. Si no se proporciona, 
                      usa la variable de entorno AZURE_KEY_VAULT_URL
        """
        self.vault_url = vault_url or os.environ.get(
            'AZURE_KEY_VAULT_URL'
        )
        
        try:
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"🔐 KeyVaultService inicializado: {self.vault_url}")
        except Exception as e:
            logger.error(f"❌ Error inicializando KeyVaultService: {str(e)}")
            raise
    
    def get_secret(self, secret_name: str) -> str:
        """
        Obtiene el valor de un secreto.
        
        Args:
            secret_name: Nombre del secreto en Key Vault
            
        Returns:
            str: Valor del secreto
            
        Raises:
            Exception: Si el secreto no existe o hay error de conexión
        """
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"✅ Secreto '{secret_name}' obtenido exitosamente")
            return secret.value
        except Exception as e:
            logger.error(f"❌ Error obteniendo secreto '{secret_name}': {str(e)}")
            raise
    
    def get_secret_as_json(self, secret_name: str) -> dict:
        """
        Obtiene un secreto y lo parsea como JSON.
        
        Args:
            secret_name: Nombre del secreto en Key Vault
            
        Returns:
            dict: Secreto parseado como diccionario
            
        Raises:
            json.JSONDecodeError: Si el secreto no es un JSON válido
            Exception: Si el secreto no existe o hay error de conexión
        """
        secret_value = self.get_secret(secret_name)
        try:
            parsed = json.loads(secret_value)
            logger.debug(f"✅ Secreto '{secret_name}' parseado como JSON")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando secreto '{secret_name}' como JSON: {str(e)}")
            raise
