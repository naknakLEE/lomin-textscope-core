# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
import torch
import numpy as np

# from maskrcnn_benchmark.structures.segmentation_mask import SegmentationMask, PolygonList
# from maskrcnn_benchmark.structures.keypoint import PersonKeypoints, IdKeypoints

from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import cascaded_union


# transpose
FLIP_LEFT_RIGHT = 0
FLIP_TOP_BOTTOM = 1


class BoxList(object):
    """
    This class represents a set of bounding boxes.
    The bounding boxes are represented as a Nx4 Tensor.
    In order to uniquely determine the bounding boxes with respect
    to an image, we also store the corresponding image dimensions.
    They can contain extra information that is specific to each bounding box, such as
    labels.
    """

    def __init__(self, bbox, image_size, mode="xyxy"):
        device = bbox.device if isinstance(bbox, torch.Tensor) else torch.device("cpu")

        if (
            not isinstance(bbox, torch.Tensor)
            or bbox.dtype != torch.float32
            or bbox.device != device
        ):
            bbox = torch.as_tensor(bbox, dtype=torch.float32, device=device)
        if bbox.ndimension() != 2:
            raise ValueError(
                "bbox should have 2 dimensions, got {}".format(bbox.ndimension())
            )
        if bbox.size(-1) != 4:
            raise ValueError(
                "last dimension of bbox should have a "
                "size of 4, got {}".format(bbox.size(-1))
            )
        if mode not in ("xyxy", "xywh"):
            raise ValueError("mode should be 'xyxy' or 'xywh'")

        self.bbox = bbox
        self.size = image_size  # (image_width, image_height)
        self.mode = mode
        self.extra_fields = {}
        # self.fields_resize = (SegmentationMask, PersonKeypoints, IdKeypoints)
        # self.fields_transpose = (SegmentationMask, PersonKeypoints, IdKeypoints)
        # self.fields_crop = (SegmentationMask, PersonKeypoints, IdKeypoints)
        # self.fields_clip = (SegmentationMask, IdKeypoints)
        self.safe_crop = {}

    def add_field(self, field, field_data):
        self.extra_fields[field] = field_data

    def set_safe_crop(self, safe_area, outer_area):
        self.safe_crop = {
            "safe_area": safe_area,
            "outer_area": outer_area,
        }

    def get_field(self, field):
        return self.extra_fields[field]

    def has_field(self, field):
        return field in self.extra_fields

    def fields(self):
        return list(self.extra_fields.keys())

    def _copy_extra_fields(self, bbox):
        for k, v in bbox.extra_fields.items():
            self.extra_fields[k] = v

    def convert(self, mode):
        if mode not in ("xyxy", "xywh"):
            raise ValueError("mode should be 'xyxy' or 'xywh'")
        if mode == self.mode:
            return self
        # we only have two modes, so don't need to check
        # self.mode
        xmin, ymin, xmax, ymax = self._split_into_xyxy()
        if mode == "xyxy":
            bbox = torch.cat((xmin, ymin, xmax, ymax), dim=-1)
            bbox = BoxList(bbox, self.size, mode=mode)
        else:
            TO_REMOVE = 1
            bbox = torch.cat(
                (xmin, ymin, xmax - xmin + TO_REMOVE, ymax - ymin + TO_REMOVE), dim=-1
            )
            bbox = BoxList(bbox, self.size, mode=mode)
        bbox._copy_extra_fields(self)
        return bbox

    def _split_into_xyxy(self):
        if self.mode == "xyxy":
            xmin, ymin, xmax, ymax = self.bbox.split(1, dim=-1)
            return xmin, ymin, xmax, ymax
        elif self.mode == "xywh":
            TO_REMOVE = 1
            xmin, ymin, w, h = self.bbox.split(1, dim=-1)
            return (
                xmin,
                ymin,
                xmin + (w - TO_REMOVE).clamp(min=0),
                ymin + (h - TO_REMOVE).clamp(min=0),
            )
        else:
            raise RuntimeError("Should not be here")

    def resize(self, size, *args, **kwargs):
        """
        Returns a resized copy of this bounding box

        :param size: The requested size in pixels, as a 2-tuple:
            (width, height).
        """

        ratios = tuple(float(s) / float(s_orig) for s, s_orig in zip(size, self.size))
        if ratios[0] == ratios[1]:
            if ratios[0] == 1:
                return self
            ratio = ratios[0]
            scaled_box = self.bbox * ratio
            bbox = BoxList(scaled_box, size, mode=self.mode)
            # bbox._copy_extra_fields(self)
            for k, v in self.extra_fields.items():
                # if not isinstance(v, torch.Tensor):
                if isinstance(v, self.fields_resize):
                    v = v.resize(size, *args, **kwargs)
                if k == "quads":
                    if len(v) > 0:
                        v = v * ratio  # N x 4 x 2
                bbox.add_field(k, v)

            return bbox

        ratio_width, ratio_height = ratios
        xmin, ymin, xmax, ymax = self._split_into_xyxy()
        scaled_xmin = xmin * ratio_width
        scaled_xmax = xmax * ratio_width
        scaled_ymin = ymin * ratio_height
        scaled_ymax = ymax * ratio_height
        scaled_box = torch.cat(
            (scaled_xmin, scaled_ymin, scaled_xmax, scaled_ymax), dim=-1
        )

        bbox = BoxList(scaled_box, size, mode="xyxy")
        if len(self.safe_crop) != 0:
            area_keys = self.safe_crop.keys()
            for _area_name in ["safe_area", "outer_area"]:
                if _area_name not in area_keys:
                    continue
                self.safe_crop[_area_name][0::2] = (
                    self.safe_crop[_area_name][0::2] * ratio_width
                ).astype(np.int32)
                self.safe_crop[_area_name][1::2] = (
                    self.safe_crop[_area_name][1::2] * ratio_height
                ).astype(np.int32)
                self.safe_crop[_area_name][0::2] = np.clip(
                    self.safe_crop[_area_name][0::2], 0, size[0] - 1
                )
                self.safe_crop[_area_name][1::2] = np.clip(
                    self.safe_crop[_area_name][1::2], 0, size[1] - 1
                )
            if (
                "safe_area" in self.safe_crop
                and "outer_area" in self.safe_crop
                and not self.safe_crop["outer_area"][3]
                >= self.safe_crop["safe_area"][3]
            ):
                import pdb

                pdb.set_trace()
            bbox.safe_crop = self.safe_crop
        # bbox._copy_extra_fields(self)
        for k, v in self.extra_fields.items():
            # if not isinstance(v, torch.Tensor):
            if isinstance(v, self.fields_resize):
                v = v.resize(size, *args, **kwargs)
            if k == "quads":
                if len(v) > 0:
                    v[:, :, 0] = v[:, :, 0] * ratio_width  # N x 4 x 2
                    v[:, :, 1] = v[:, :, 1] * ratio_height  # N x 4 x 2
            bbox.add_field(k, v)

        return bbox.convert(self.mode)

    def to(self, device):
        bbox = BoxList(self.bbox.to(device), self.size, self.mode)
        for k, v in self.extra_fields.items():
            if hasattr(v, "to"):
                v = v.to(device)
            bbox.add_field(k, v)
        return bbox

    def __getitem__(self, item):
        if isinstance(item, torch.Tensor):
            item_np = item.cpu().numpy()
        elif isinstance(item, np.ndarray):
            item_np = item
            item = torch.tensor(item)
            if item.dtype == np.uint8:
                item_np = np.array(item_np, dtype=np.bool)
        elif isinstance(item, int):
            item = torch.tensor([item], dtype=torch.long)
            item_np = item.numpy()
        else:
            raise NotImplementedError
        if isinstance(self.bbox, np.ndarray):
            item = item.numpy()
        bbox = BoxList(self.bbox[item], self.size, self.mode)
        for k, v in self.extra_fields.items():
            # if isinstance(v, (torch.Tensor, SegmentationMask, PersonKeypoints, IdKeypoints)):
            #     bbox.add_field(k, v[item])
            # el
            if isinstance(v, np.ndarray):
                bbox.add_field(k, v[item_np])
            elif isinstance(v, list):
                # assert len(v) == len(item_np), "k:{}, v:{}, item_np:{}".format(k, len(v), len(item_np))
                assert item_np.ndim == 1
                if item_np.dtype in [np.bool, np.uint8]:
                    bbox.add_field(k, [el for el, _k in zip(v, item_np) if _k])
                elif item_np.dtype in [np.int32, np.int64]:
                    bbox.add_field(k, [v[_] for _ in item_np])
                else:
                    raise NotImplementedError
            else:
                raise NotImplementedError
        return bbox

    def __len__(self):
        return self.bbox.shape[0]

    def area(self):
        box = self.bbox
        if self.mode == "xyxy":
            TO_REMOVE = 1
            area = (box[:, 2] - box[:, 0] + TO_REMOVE) * (
                box[:, 3] - box[:, 1] + TO_REMOVE
            )
        elif self.mode == "xywh":
            area = box[:, 2] * box[:, 3]
        else:
            raise RuntimeError("Should not be here")

        return area

    def copy_with_fields(self, fields, skip_missing=False):
        bbox = BoxList(self.bbox, self.size, self.mode)
        if len(self.safe_crop) != 0:
            bbox.safe_crop = self.safe_crop
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        for field in fields:
            if self.has_field(field):
                bbox.add_field(field, self.get_field(field))
            elif not skip_missing:
                raise KeyError("Field '{}' not found in {}".format(field, self))
        return bbox

    def merge_other_boxlist(self, boxlist):
        # assert boxlist.size == self.size
        # assert boxlist.mode == self.mode
        assert set(boxlist.fields()) == set(self.fields())

        merged_boxlist = BoxList(
            torch.cat((self.bbox, boxlist.bbox), dim=0), self.size, self.mode
        )
        # if len(self.safe_crop) != 0:
        #     bbox.safe_crop = self.safe_crop
        for k, v in self.extra_fields.items():
            if isinstance(v, torch.Tensor):
                v_cat = torch.cat((v, boxlist.get_field(k)), dim=0)
            elif isinstance(v, np.ndarray):
                v_cat = np.concatenate((v, boxlist.get_field(k)), axis=0)
            elif isinstance(v, list):
                v_cat = v + boxlist.get_field(k)
            # elif isinstance(v, SegmentationMask):
            #     if isinstance(v.instances, PolygonList):
            #         v_cat = v
            #         v_cat.instances.polygons.extend(boxlist.get_field(k).instances.polygons)
            #     else:
            #         raise NotImplementedError
            # elif isinstance (v, PersonKeypoints):
            #     raise NotImplementedError
            else:
                raise NotImplementedError
            assert len(merged_boxlist) == len(v_cat)
            merged_boxlist.add_field(k, v_cat)
        return merged_boxlist

    def __repr__(self):
        s = self.__class__.__name__ + "("
        s += "num_boxes={}, ".format(len(self))
        s += "image_width={}, ".format(self.size[0])
        s += "image_height={}, ".format(self.size[1])
        s += "mode={})".format(self.mode)
        return s
