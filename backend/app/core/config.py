from pydantic_settings import BaseSettings
from typing import Optional
import os

def get_gcp_secret(secret_name: str) -> Optional[str]:
    """Obtiene un secreto de Google Cloud Secret Manager"""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', os.environ.get('GCP_PROJECT_ID'))
        if not project_id:
            return None
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Could not get secret {secret_name}: {e}")
        return None

class Settings(BaseSettings):
    # App
    APP_NAME: str = "CryptoFlow"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cryptoflow"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Exchange (Binance) - Legacy
    EXCHANGE_API_KEY: Optional[str] = None
    EXCHANGE_API_SECRET: Optional[str] = None
    EXCHANGE_TESTNET: bool = True
    
    # Coinbase
    COINBASE_API_KEY_NAME: Optional[str] = None
    COINBASE_PRIVATE_KEY: Optional[str] = None
    
    # GCP
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    
    # ML
    ML_MODEL_PATH: str = "./ml_models"
    AUTO_RECALIBRATE: bool = True
    RECALIBRATE_INTERVAL_HOURS: int = 24
    
    class Config:
        env_file = ".env"

# Initialize settings
settings = Settings()

# Try to load Coinbase credentials from GCP Secret Manager if not set
if not settings.COINBASE_API_KEY_NAME:
    secret_value = get_gcp_secret('coinbase_api_key_name')
    if secret_value:
        settings.COINBASE_API_KEY_NAME = secret_value

if not settings.COINBASE_PRIVATE_KEY:
    secret_value = get_gcp_secret('coinbase_private_key')
    if secret_value:
        settings.COINBASE_PRIVATE_KEY = secret_value
