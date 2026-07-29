from pydantic_settings import BaseSettings
class DemandSettings(BaseSettings):
    default_horizon: int = 30
    retrain_interval: int = 86400
settings = DemandSettings()
