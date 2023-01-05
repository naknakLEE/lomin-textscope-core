
from app.utils.logging import logger

from apscheduler.schedulers.background import BackgroundScheduler 


def register_cron(args=[],**kwargs):
    flag = False
    
    # init background scheduler for running deletion job
    scheduler = BackgroundScheduler()

    # get want to croning function name
    func=kwargs.get("function")

    kwargs_wrapper=kwargs.get("kwargs", [])

    if func.__name__ == None:
        return

    try:
        # Manually configure 
        if func.__name__ == 'delete_data_after_days':
            session = kwargs.get("session")
            
            # must has session
            if session == None:
                logger.error(f"Job Failed: \n\tfunction:{func.__name__}\n\tdetail:DB Session is not defined")
                return
            args.append(session)
            #TODO: cron 실행시점 .env로 관리 필요
            scheduler.add_job(func, 'cron', [session], kwargs={"life_days":kwargs["life_days"]},\
                hour='0', minute='0', second='0')
            logger.info(f"Job added: {func.__name__}")
            flag = True

        # Auto config and default:  매일 자정 실행
        else:
            scheduler.add_job(func, 'cron', args=args, kwargs=kwargs, hour='0')
            logger.info(f"Job added: {func.__name__}")
            flag = True

    except Exception as e:
        logger.error(f"Job Failed: \n\tfunction:{func.__name__}\n\tdetail:{e}")

    if flag is True:
        scheduler.start()