from lovit.postprocess import idcard
import onnx
from os import path

from bentoml_textscope.idcard_model_service import IdcardModelService
from bentoml_textscope.common.const import get_settings
from bentoml_textscope.utils.utils import load_json


settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["idcard"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(
        settings.BASE_PATH, settings.INFERENCE_SERVER_APP_NAME, cfg["model_path"]
    )


# Create a pytorch model service instance
idcard_model_service = IdcardModelService()

# Pack the newly trained model artifact
boundary_detection_model = onnx.load(f"{model_path['boundary_model']}")
kv_detection_model = onnx.load(f"{model_path['kv_model']}")
recognition_model = onnx.load(f"{model_path['recognition_model']}")
idcard_model_service.pack("boundary_detection", boundary_detection_model)
idcard_model_service.pack("kv_detection", kv_detection_model)
idcard_model_service.pack("recognition", recognition_model)
# idcard_model_service.set_version("2021-06.textscope")

# Save the prediction service to disk for model serving
idcard_model_service.save()
# idcard_model_service.save_to_dir('/root/bentoml/repository/IdcardModelService')


############################ for debugging ############################

# import PIL
# import numpy as np
# from bentoml_textscope.utils.utils import read_all_tiff_pages

# image_dir = f"{settings.BASE_PATH}/others/assets/000000000000000IMG_4825.jpg"
# img = PIL.Image.open(image_dir)
# img = np.array(img)
# idcard_model_service.inference(img)

# image_path = "/workspace/others/assets/generation_multipagetiff.tiff"
# # image_path = "/workspace/others/assets/tif_test.tif"
# data = {
#     "image_path": image_path,
#     "request_id": "sdfasfdasdf",
#     "page": 3,
#     # "doc_type": [
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "ZZ",
#     #     "A3",
#     #     "A1",
#     #     "A1",
#     #     "A1",
#     #     "TT",
#     #     "A1",
#     #     "A7",
#     #     "E2",
#     #     "EZ",
#     #     "EZ",
#     #     "EZ",
#     #     "EZ",
#     #     "EZ",
#     # ],
# }
# result = idcard_model_service.tiff_inference([data])
# # result = idcard_model_service.tiff_inference_all([data])
# print("result", result)
# # responst: {0: {'doc_type': 'ZZ'}, 1: {'doc_type': 'ZZ'}, 2: {'issue_date': '2019-2-9', 'dlc_serial_num': 'UF8T9T', 'id': '', 'name': '', 'doc_type': 'ZZ'}, 3: {'dlc_license_num': '20-98-602499-40', 'id': '740528', 'name': '이불*', 'issue_date': '2018-10-17', 'dlc_serial_num': '8HWVO4', 'doc_type': 'ZZ'}, 4: {'expiration_date': '1476-1-1', 'id': '', 'issue_date': '', 'name': '', 'doc_type': 'ZZ'}, 5: {'doc_type': 'ZZ'}, 6: {'doc_type': 'ZZ'}}
