# import cv2

# API_ADDR = "v1/inference/pipeline"
# URL = f"http://web:{settings.WEB_IP_PORT}/{API_ADDR}"

# image_dir = "./others/assets/000000000000000IMG_4825.jpg"
# img = cv2.imread(image_dir)
# _, img_encoded = cv2.imencode(".jpg", img)
# img_bytes = img_encoded.tobytes()

# files = {"image": ("test.jpg", img_bytes)}


# async def request(client):
#     response = await client.post(URL, files=files, timeout=30.0)
#     return response.text


# async def task():
#     async with httpx.AsyncClient() as client:
#         tasks = [request(client) for _ in range(10)]
#         result = await asyncio.gather(*tasks)
#         print("\033[95m" + f"{result}" + "\033[m")


# @router.get("/async_test")
# async def async_test():
#     await task()


# @router.get("/get_asyncio_sleep")
# async def achyncio_sleep():
#     await asyncio.sleep(3)
#     return "Complete"
