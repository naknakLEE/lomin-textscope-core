import os
import time
import copy
import numpy as np

from httpx import Client
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import ImageDraw, ImageFont, Image

from lovit.agamotto.data.transforms import apply_augmentations
from lovit.agamotto.preprocess import build_transforms

from app import ray
from app.wrapper import pp
from app.utils.utils import load_image, print_error_log, save_debug_img, bcolors
from app.common.const import get_settings


settings = get_settings()


@ray.remote
class Visualizer(object):
    def __init__(self):
        pass

    def save_vis_image_to_db(
        self,
        request_id: str,
        save_path: str,
        inference_type: str,
        visualization_type: str,
    ) -> None:
        try:
            data = {
                "task_id": request_id,
                "inference_img_path": save_path,
                "inference_type": inference_type,
                "visualization_type": visualization_type,
            }
            with Client() as client:
                response = client.post(
                    url="http://localhost:8000/dao/create/visualize", json=data
                )
            print(bcolors.BOLD + f"insert vis: {response.text}" + bcolors.ENDC)
        except Exception as ex:
            print_error_log()

    def revert_size(self, boxes, current_size, original_size):
        if current_size == original_size:
            return boxes
        x_ratio = original_size[0] / current_size[0]
        y_ratio = original_size[1] / current_size[1]
        boxes[:, 0::2] = boxes[:, 0::2] * x_ratio
        boxes[:, 1::2] = boxes[:, 1::2] * y_ratio
        return boxes

    def resize_image(self, image: np.array, detection_boxes: List) -> Tuple[List, np.array]:
        transforms = build_transforms(
            min_size=1800,
            max_size=2000,
        )
        original_image_size = image.shape
        if original_image_size[0] < 2000 and original_image_size[1] < 2000:
            image = np.ascontiguousarray(apply_augmentations(transforms, image)[0])
            detection_boxes = self.revert_size(
                np.array(detection_boxes),
                (original_image_size[1], original_image_size[0]),
                (image.shape[1], image.shape[0]),
            ).astype(np.int32)
        return (detection_boxes, image)

    def detection_result_visualization(
        self,
        image: np.array,
        detection_boxes: List,
        detection_classes: List,
        detection_scores: List,
        texts: List,
        request_id: str,
        image_path,
        save_dir,
        model_name,
    ) -> None:
        # Expand image size if image size is small
        if save_dir is None:
            save_dir = os.path.join(
                settings.TEXTSCOPE_LOG_DIR_PATH,
                "debug",
                time.strftime("%Y%m%d"),
                "detection",
            )
        vis_type_list = list(
            map(lambda x: x.strip(), "split_screen,overlay".split(","))
        )
        print(bcolors.BOLD + "vis type list: {}".format(vis_type_list) + bcolors.ENDC)

        detection_boxes, image = self.resize_image(
            image=image, detection_boxes=detection_boxes
        )
        for vis_type in vis_type_list:
            current_datetime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if image_path is not None and model_name is not None:
                filename = (
                    f"{Path(image_path).stem}_{request_id}_{current_datetime}.png"
                )
                save_path = Path(save_dir, model_name, vis_type, filename)
            elif image_path is not None:
                filename = (
                    f"{Path(image_path).stem}_{request_id}_{current_datetime}.png"
                )
                save_path = Path(save_dir, vis_type, filename)
            else:
                filename = f"{request_id}_{current_datetime}.png"
                save_path = Path(save_dir, vis_type, filename)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            print(
                bcolors.BOLD
                + "vis type: {}, save path: {}".format(vis_type, save_path)
                + bcolors.ENDC
            )
            save_debug_img(
                img_arr=image,
                boxes=detection_boxes,
                classes=detection_classes,
                scores=detection_scores,
                texts=texts,
                savepath=save_path.as_posix(),
                inference_type=vis_type,
            )
            inference_type = "gocr" if detection_classes[0] == "text" else "kv"
            self.save_vis_image_to_db(
                request_id=request_id,
                save_path=save_path.as_posix(),
                inference_type=inference_type,
                visualization_type=vis_type,
            )

    def recognition_result_visualization(
        self, cropped_images: List, texts: List, request_id: str
    ) -> List:
        debugging_croped_images = copy.deepcopy(cropped_images)

        right = 30
        left = 30
        top = 30
        bottom = 30

        font = ImageFont.truetype(
            os.path.join(
                "/workspace",
                "assets",
                "gulim.ttc",
            ),
            16,
        )

        for i, (image, text) in enumerate(zip(debugging_croped_images, texts)):
            image = Image.fromarray((image * 255).transpose(1, 2, 0).astype(np.uint8))
            width, height = image.size
            new_width = width + right + left
            new_height = height + top + bottom

            result = Image.new(image.mode, (new_width, new_height), (0, 0, 0))
            result.paste(image, (left, top))

            draw = ImageDraw.Draw(result)
            draw.text((30, 0), text, (256, 256, 256), font=font)

            savepath = f"{request_id}_{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}_deidentify_image.jpg"
            info_save_dir = os.path.join(
                "/workspace/logs", "debug", time.strftime("%Y%m%d"), "recognition"
            )
            os.makedirs(info_save_dir, exist_ok=True)
            info_save_path = os.path.join(info_save_dir, os.path.basename(savepath))

            result.save(info_save_path)

    def parse_input_data(self, result, inputs, angle):
        if "kv" in result:
            result = result.get("kv")
        else:
            if "texts" not in result:
                with Client() as client:
                    status_code, texts = pp.convert_preds_to_texts(
                        client=client,
                        rec_preds=result.get("rec_preds", []),
                    )
                result["texts"] = texts if status_code == 200 else []

        classes = list()
        texts = list()
        boxes = list()
        scores = list()
        if "boxes" in result:
            classes = result.get("classes")
            texts = result.get("texts")
            boxes = result.get("boxes")
            scores = result.get("scores")
        else:
            for key, values in result.items():
                if isinstance(values, list):
                    for value in values:
                        if not isinstance(value.get("bboxes"), list):
                            continue
                        for bbox in value.get("bboxes"):
                            boxes.append(bbox)
                            texts.append(value.get("text"))
                            classes.append("{} {}".format(key, value.get("text")))
                elif isinstance(values, dict):
                    boxes.append(values.get("box"))
                    texts.append(values.get("text"))
                    classes.append(values.get("class"))
                    scores.append(values.get("score"))

        image_array = load_image(
            {"image_path": inputs.get("image_path"), "page": inputs.get("page", 1)}
        )
        pil_image = Image.fromarray(image_array)
        rotated_image = pil_image.rotate(angle, expand=True)
        image_array = np.asarray(rotated_image)
        inputs = {
            "image": image_array,
            "detection_boxes": boxes,
            "detection_classes": classes,
            "detection_scores": scores if len(scores) > 0 else None,
            "texts": texts,
            "request_id": inputs.get("request_id"),
            "image_path": inputs.get("image_path"),
            "save_dir": None,
            "model_name": "web",
        }
        return inputs

    def save_vis_image(
        self,
        result: Dict,
        inputs: Dict,
        anlge: 0.0,
    ):
        parsed_data = self.parse_input_data(result, inputs, anlge)
        self.detection_result_visualization(**parsed_data)


visualizer = Visualizer.options(max_concurrency=2).remote()
