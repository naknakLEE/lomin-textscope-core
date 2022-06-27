class HTTPBearerFake(): # 토큰 사용 on/off를 위해 사용
    async def __call__(self) -> None :
        return None