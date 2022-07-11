
import cv2
import math
import numpy as np

from PIL import Image
from typing import Dict, List, Optional, Union


def warp_bboxes_to_origin(bboxes, transform_matrix):
    result = dict()
    if not transform_matrix:
        return []
    inverse_transform_matrix = np.linalg.pinv(transform_matrix)

    # Warp bboxes to origin coordinates
    all_boxes_x = []
    all_boxes_y = [] 
    for bbox in bboxes:
        # Map bbox to points
        x1 = bbox[0]
        x2 = bbox[2]
        y1 = bbox[1]
        y2 = bbox[3]
        points = np.array([[[x1,y1], [x1,y2], [x2,y2], [x2,y1]]], dtype=np.float32)

        # Perspective transform
        points =  cv2.perspectiveTransform(points, inverse_transform_matrix)

        # Map points to all_points        
        all_points_x = []
        all_points_y = []
        for id in range (len(points[0])):
            all_points_x.append(float(points[0][id][0]))
            all_points_y.append(float(points[0][id][1]))
        all_boxes_x.append(all_points_x)
        all_boxes_y.append(all_points_y)

    result["all_boxes_x"] = all_boxes_x
    result["all_boxes_y"] = all_boxes_y
    return result

def dot4_to_rectangle(all_boxes_x, all_boxes_y):
    rectangle = []
    for xs, ys in zip(all_boxes_x, all_boxes_y):
        x1 = min(xs)
        x2 = max(xs)
        y1 = min(ys)
        y2 = max(ys)
        rectangle.append([x1, y1, x2, y2])
    return rectangle
    
    


def get_unmodified_bbox(input: Dict):
    if input.get("doc_type") == "idcard":
        kv_box = {}
        if "kv" in input:
            for key, value in input.get("kv").items():
                
                if isinstance(value, dict):
                    kv_box[key] = value.get("box", [])
            if kv_box:
                unmodified_all_box = warp_bboxes_to_origin(kv_box.values(), input.get("transform_matrix"))
                all_boxes_x = unmodified_all_box.get("all_boxes_x")
                all_boxes_y = unmodified_all_box.get("all_boxes_y")
                unmodified_bbox = dot4_to_rectangle(all_boxes_x, all_boxes_y)
                
                for key, nmbbox in zip(kv_box.keys(), unmodified_bbox):
                    input["kv"][key]["unmodified_bbox"] = nmbbox
                
        if input.get("boxes"):
            unmodified_all_box = warp_bboxes_to_origin(input.get("boxes"), input.get("transform_matrix"))
            all_boxes_x = unmodified_all_box.get("all_boxes_x")
            all_boxes_y = unmodified_all_box.get("all_boxes_y")
            unmodified_bbox = dot4_to_rectangle(all_boxes_x, all_boxes_y)
            input["unmodified_bbox"] = unmodified_bbox
    else:
        kv_box = {}
        if "kv" in input:
            for key, value in input.get("kv").items():
                if isinstance(value, dict):
                    kv_box[key] = value.get("box", [])
                    
            unmodified_bbox = reverse_rotated_bbox(
                input.get("image_width_origin"), 
                input.get("image_height_origin"),
                input.get("angle"),
                kv_box.values()
                )
            for key, nmbbox in zip(kv_box.keys(), unmodified_bbox):
                input["kv"][key]["unmodified_bbox"] = nmbbox
        
        unmodified_bbox = reverse_rotated_bbox(
            input.get("image_width_origin"), 
            input.get("image_height_origin"),
            input.get("angle"),
            input.get("boxes"))
        input["unmodified_bbox"] = unmodified_bbox
        
    return input
        
        
    

def reverse_rotated_coord(x, y, angle, origin_center, rot_center):
    # 각도를 라디안 각도로 구하기
    # 삼각 함수 사용할 때 라디안 사용
    rad = angle * math.pi / 180.0

    # 센터 좌표 구하기
    (rot_center_x, rot_center_y) = rot_center
    (ori_center_x, ori_center_y) = origin_center

    # 이미지 좌표 -> 0점 좌표로 보정
    zero_x = x - rot_center_x
    zero_y = y - rot_center_y

    # 계산식을 이용해서 돌린 좌표 구하기
    x1 = math.cos(rad)*zero_x - math.sin(rad)*zero_y
    y1 = math.sin(rad)*zero_x + math.cos(rad)*zero_y

    # 0점 좌표를 이용해서 구한 좌표이기 때문에 이미지 좌표로 변환 필요
    x1+= rot_center_x
    y1+= rot_center_y

    # 오프셋 맞추는 작업
    # 중심좌표 원본이미지에 이동시키기
    
    offset_x = rot_center_x - ori_center_x
    offset_y = rot_center_y - ori_center_y

    origin_x = x1 - offset_x
    origin_y = y1 - offset_y
    return origin_x, origin_y

def reverse_rotated_bbox(origin_w, origin_h, angle, boxes):
    
    res = []
    origin_img = Image.new('RGB', (origin_w, origin_h))
    rot_pil_img = origin_img.rotate(angle, expand=True)
    (rot_w, rot_y) = rot_pil_img.size
    rot_center = (rot_w / 2, rot_y / 2)
    
    (origin_w, origin_h) = origin_img.size
    origin_center = (origin_w / 2, origin_h / 2)
    
    for box in boxes:
        x1, y1 = reverse_rotated_coord(box[0], box[1], angle, origin_center, rot_center)
        x2, y2 = reverse_rotated_coord(box[2], box[3], angle, origin_center, rot_center)
        res.append([x1, y1, x2, y2])
    return res