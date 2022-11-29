import os
import uvicorn

from minio import Minio
from app.common.const import get_settings
from app.utils.create_app import app_generator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.utils.logging import logger
from datetime import date, timedelta
from app.utils.minio import MinioService
from app.database.query import delete_nak_data
from app.database.connection import db
from app import hydra_cfg

settings = get_settings()
app = app_generator()


@app.on_event("startup")
async def startup_event():
    os.environ["IS_READY"] = "true"


args = {
    "app": "main:app",
    "host": "0.0.0.0",
    "port": settings.WEB_IP_PORT,
    "workers": settings.TEXTSCOPE_CORE_WORKERS,
}
if settings.DEVELOP:
    args["reload"] = True

sched = AsyncIOScheduler()
minio_client = MinioService()

async def remove_data_job():
    """
        Minio삭제 및 Database 삭제 job 등록
    """
    today = date.today()
    logger.debug(f"=====================> {today.isoformat()} Remove Data Job Start")

    delete_date = today - timedelta(2)
    delete_date = delete_date.isoformat()
        
    # 1. Inference_result 및 document_info 삭제
    result = delete_nak_data(session=next(db.session()), date_time_str=delete_date)    
    if(result == False): return

    # 1-2. 검수가 안된 파일(1에서 진행한 result값에)이 있을경우 Minio -> /CAMS/OCR/RESPDF 경로로 업로드
    if(len(result)): minio_client.move_file_to_local_directory(bucket_name=settings.MINIO_IMAGE_BUCKET, document_path_list=result, local_directory=hydra_cfg.document.no_update_directory)

    # 3. Minio 삭제
    minio_client.remove(bucket_name=settings.MINIO_IMAGE_BUCKET, object_name=delete_date)

    logger.debug(f"=====================> {today.isoformat()} Remove Data Job Finish")
# schedule regist
sched.add_job(remove_data_job, trigger='cron', hour='09', minute='56')
sched.start()

if __name__ == "__main__":
    uvicorn.run(**args)
