from io import BytesIO

# Optional MinIO for artifact storage
try:
    from minio import Minio
except Exception:  # pragma: no cover
    Minio = None  # type: ignore

from ..core.config import settings


def get_minio_client():
    if Minio is None:
        return None
    try:
        use_secure = settings.MINIO_ENDPOINT.startswith("https://")
        endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        client = Minio(endpoint, access_key=settings.MINIO_ACCESS_KEY, secret_key=settings.MINIO_SECRET_KEY, secure=use_secure)
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
        return client
    except Exception:
        return None


def put_artifact(client, key: str, data: bytes):
    if not client:
        return False
    try:
        client.put_object(settings.MINIO_BUCKET, key, BytesIO(data), length=len(data))
        return True
    except Exception:
        return False
