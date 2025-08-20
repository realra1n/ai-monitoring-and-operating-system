import os


class Settings:
    GRAFANA_URL: str = os.environ.get("GRAFANA_URL", "http://localhost:3000")
    MINIO_ENDPOINT: str = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.environ.get("MINIO_ACCESS_KEY", "minio")
    MINIO_SECRET_KEY: str = os.environ.get("MINIO_SECRET_KEY", "minio123")
    MINIO_BUCKET: str = os.environ.get("MINIO_BUCKET", "artifacts")
    DEMO_TENANT: str = "demo"


settings = Settings()
