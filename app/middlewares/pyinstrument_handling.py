import datetime
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response
from pyinstrument import Profiler

class Profiling_Middleware_Pyinstrument(BaseHTTPMiddleware):
    def __init__(self, 
                app,
                async_mode: str = "enable",
                interval: float = 0.001,
                save_html: bool = True):
        """ Pyinstrument를 이용한 Profiling Middleware

        Args:
            app (_type_):               기본 파라미터
            async_mode (str, optional): "enable", "disable", "strict". Defaults to "enable".
                                        https://pyinstrument.readthedocs.io/en/latest/reference.html#pyinstrument.Profiler.async_mode
            interval (float, optional): 더 자세한 정보를 얻으려면 interval의 소수점을 늘리면 된다. 다만 속도가 너무 느려질 수 있다.
            save_html (bool, optional): html 파일로 저장할지 여부. Defaults to False.
        """
        super().__init__(app)
        self.async_mode = async_mode
        self.interval = interval
        self.save_html = save_html
        
        
        
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        profiler = Profiler(async_mode=self.async_mode, interval = self.interval)
        profiler.start()
        res = await call_next(request)
        profiler.stop()
        profiler.print(unicode=True, color=True, show_all=True, timeline=True)
        if self.save_html:
            now = datetime.datetime.now()
            nowTime = now.strftime('%H:%M:%S')
            file_name = f"{request.method}_{request.url.path}_{nowTime}.html"
            results_file = file_name.replace("/", "_")
            with open(results_file, "w", encoding="utf-8") as f_html:
                f_html.write(profiler.output_html())
        return res