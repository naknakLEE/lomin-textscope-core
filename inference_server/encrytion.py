from os import path

from inference_server.common.const import get_settings
from inference_server.utils.utils import load_json
from lovit.crypto.utils import encrypt_dir
from lovit.crypto.crypto import Crypto

settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])


encrypt_path = "/root/bentoml/repository/DocumentModelService/v1/DocumentModelService/artifacts"

crypto = Crypto()
key = settings.CRYPTO_KEY  # key = crypto.generate_key()
encrypt_dir(encrypt_path, key=key, prefix=settings.CRYPTO_PREFIX, filter=None, remove=True)


# detection_model = torch.jit.load(f"{model_path['detection_model']}")

# image_dir = f"{settings.BASE_PATH}/others/assets/basic_cert2.jpg"
# img = PIL.Image.open(image_dir)
# img = np.array(img)
# img = np.transpose(img, (2, 0, 1))
# img = torch.from_numpy(img.copy())
# with torch.no_grad():
#     reuslt = detection_model(img)
# print("\033[95m" + f"{reuslt[0].shape}" + "\033[m")
