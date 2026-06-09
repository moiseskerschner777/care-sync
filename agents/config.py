from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "production"
    iris_host: str = ""
    iris_port: int = 1972
    iris_namespace: str = "USER"
    iris_username: str = ""
    iris_password: str = ""
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_api_base: str = ""
    embedding_provider: str = ""
    embedding_api_key: str = ""
    embedding_api_base: str = ""
    codebase_mcp_url: str = "http://python-code-rag:8005/sse"
    iris_mcp_url: str = "http://mcp-database-server-iris:3001"
    fhir_base_url: str = Field(default="http://iris:52773/fhir/r4")

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
