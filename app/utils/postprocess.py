
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
    


def revert_crop_img_from_bbox(
        origin_width,  
        origin_height, 
        crop_coord,
        bbox,
    ):
    """
        origin_width:int,  원본 이미지 가로
        origin_height:int, 원본 이미지 세로
        crop_coord:List[int, int, int, int], 원본 이미지에서 crop 좌표
        bbox = List[List[int, int, int, int]]): crop 이미지에서 detecting된 좌표
        
        example
            origin_width = 1920
            origin_height = 1080
            crop_coord = [ 44.2151,   4.6654, 308.5250, 513.0000]
            bbox = [[0.0, 0.0, 50.1, 100.20], [4.0, 5.55, 100.1, 200.20]]
            
        return [[0.0, 0.0, 50.1, 100.20], [4.0, 5.55, 100.1, 200.20]] <- bbox를 crop이전(원본 이미지)에서 bbox로 나타낼 수 있도록 표현
        
    """
    x_offset, y_offset = crop_coord[:2]
    res = [
        [x1+x_offset,y1+y_offset,x2+x_offset,y2+y_offset] 
        for x1,y1,x2,y2 in bbox
    ]
    return res


def get_unmodified_bbox(input: Dict):
    if input.get("doc_type") == "idcard":
        kv_box = {}
        boundary_coord = input.get("boundary_coord")
        if "kv" in input:
            for key, value in input.get("kv").items():
                if isinstance(value, dict) and value:
                    kv_box[key] = value.get("box", [])
            
            if boundary_coord:
                # crop 된 image 원본 size image로 돌리기 
                crop_kv_box  = revert_crop_img_from_bbox(
                    input.get("image_width_origin"),
                    input.get("image_height_origin"),
                    boundary_coord,
                    kv_box.values()
                )
                for key, c_box in zip(kv_box.keys(), crop_kv_box):
                    kv_box[key] = c_box
            
            # 회돈 된 image 원본 이지로 돌리기
            unmodified_bbox = reverse_rotated_bbox(
                input.get("image_width_origin"), 
                input.get("image_height_origin"),
                input.get("angle"),
                kv_box.values()
                )
            for key, nmbbox in zip(kv_box.keys(), unmodified_bbox):
                input["kv"][key]["unmodified_box"] = nmbbox
        
        
        if boundary_coord:
            crop_kv_box  = revert_crop_img_from_bbox(
                input.get("image_width_origin"),
                input.get("image_height_origin"),
                boundary_coord,
                input.get("boxes")
            )
        unmodified_bbox = reverse_rotated_bbox(
            input.get("image_width_origin"), 
            input.get("image_height_origin"),
            input.get("angle"),
            crop_kv_box)
        input["unmodified_box"] = unmodified_bbox
        
        # TODO 아래 주석은 4dot unmodified box를 구하는 좌표입니다.
        # 신분증에서 4dot detection를 사용하게 된다면, 아래 주석을 해제하고 사용.
        # 
        # kv_box = {}
        # if "kv" in input:
        #     for key, value in input.get("kv").items():
                
        #         if isinstance(value, dict):
        #             kv_box[key] = value.get("box", [])
        #     if kv_box:
        #         unmodified_all_box = warp_bboxes_to_origin(kv_box.values(), input.get("transform_matrix"))
        #         all_boxes_x = unmodified_all_box.get("all_boxes_x")
        #         all_boxes_y = unmodified_all_box.get("all_boxes_y")
        #         unmodified_bbox = dot4_to_rectangle(all_boxes_x, all_boxes_y)
                
        #         for key, nmbbox in zip(kv_box.keys(), unmodified_bbox):
        #             input["kv"][key]["unmodified_box"] = nmbbox
                
        # if input.get("boxes"):
        #     unmodified_all_box = warp_bboxes_to_origin(input.get("boxes"), input.get("transform_matrix"))
        #     all_boxes_x = unmodified_all_box.get("all_boxes_x")
        #     all_boxes_y = unmodified_all_box.get("all_boxes_y")
        #     unmodified_bbox = dot4_to_rectangle(all_boxes_x, all_boxes_y)
        #     input["unmodified_box"] = unmodified_bbox
    else:
        kv_box = {}
        if "kv" in input:
            for key, value in input.get("kv").items():
                if isinstance(value, dict) and value:
                    kv_box[key] = value.get("box", [])
                    
            unmodified_bbox = reverse_rotated_bbox(
                input.get("image_width_origin"), 
                input.get("image_height_origin"),
                input.get("angle"),
                kv_box.values()
                )
            for key, nmbbox in zip(kv_box.keys(), unmodified_bbox):
                input["kv"][key]["unmodified_box"] = nmbbox
        
        unmodified_bbox = reverse_rotated_bbox(
            input.get("image_width_origin"), 
            input.get("image_height_origin"),
            input.get("angle"),
            input.get("boxes"))
        input["unmodified_box"] = unmodified_bbox
        
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
        x_tl, y_tl = reverse_rotated_coord(box[0], box[1], angle, origin_center, rot_center)
        x_br, y_br = reverse_rotated_coord(box[2], box[3], angle, origin_center, rot_center)
        
        x_tr, y_tr = reverse_rotated_coord(box[2], box[1], angle, origin_center, rot_center)
        x_bl, y_bl = reverse_rotated_coord(box[0], box[3], angle, origin_center, rot_center)
        
        x1 = min(x_tl, x_br, x_tr, x_bl)
        y1 = min(y_tl, y_br, y_tr, y_bl)
        x2 = max(x_tl, x_br, x_tr, x_bl)
        y2 = max(y_tl, y_br, y_tr, y_bl)
        
        res.append([x1, y1, x2, y2])
    return res