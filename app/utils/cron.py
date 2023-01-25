
from apscheduler.schedulers.background import BackgroundScheduler

from app.utils.logging import logger


def register_cron(function, args=[],**kwargs):
    """input으로 들어온 function을 cron으로 등록해주는 함수
        function의 이름을 기준으로, 다른 로직을 실행한다.

    Args:
        function (function): cron으로 등록할 function argument.
        args (list, optional): cron 등록 대상의 function 실행 시, 첨부할 argument. Defaults to [].
    """    
    flag = False
    
    # init background scheduler for running deletion job
    scheduler = BackgroundScheduler()

    # get want to croning function name
    
    func = function
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
            
            #TODO: cron 실행시점 .env로 관리 필요
            scheduler.add_job(func, 'cron', kwargs=kwargs,\
                hour='0', minute='0', second='0')
                # second='0')

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