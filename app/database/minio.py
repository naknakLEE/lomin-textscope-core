from minio import Minio
from minio.commonconfig import Filter, ENABLED

from app.config import settings


def connect_minio():
    """
        Object Storage인 Minio를 연결합니다.
    """
    minio_endpoint = "{}:{}".format(settings.MINIO_IP_ADDR, settings.MINIO_IP_PORT)
    mc = Minio(
        minio_endpoint,
        secure=False,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        region='kr'
    )
    if not mc.bucket_exists(settings.MINIO_IMAGE_BUCKET):
        mc.make_bucket(settings.MINIO_IMAGE_BUCKET)

    # 이전 Minio 라이프사이클이 있을경우 이전 사이클 삭제
    if mc.get_bucket_lifecycle(settings.MINIO_IMAGE_BUCKET):
        mc.delete_bucket_lifecycle(settings.MINIO_IMAGE_BUCKET)

    # Minio 라이프사이클 사용할 경우 라이프사이클 적용
    if settings.MINIO_LIFE_CYCLE_ENABLED == ENABLED:
        from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration
        life_cycle_config = LifecycleConfig(
            [
                Rule(
                    settings.MINIO_LIFE_CYCLE_ENABLED,
                    rule_filter=Filter(prefix=f"{settings.MINIO_IMAGE_BUCKET}/"),
                    rule_id=settings.MINIO_LIFE_CYCLE_RULE_ID,
                    expiration=Expiration(days=settings.MINIO_LIFE_CYCLE_DAYS)
                )
            ]
        )
        mc.set_bucket_lifecycle(settings.MINIO_IMAGE_BUCKET, life_cycle_config)
        
mc = connect_minio()