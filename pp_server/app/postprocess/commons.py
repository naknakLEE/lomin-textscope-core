import re
import copy
import torch
import numpy as np
from tqdm import tqdm
from shapely.geometry import Polygon
from maskrcnn_benchmark.structures.boxlist_ops import boxlist_iou, remove_small_boxes
from maskrcnn_benchmark.modeling.roi_heads.mask_head.inference import Masker
from maskrcnn_benchmark.data.utils import mask_to_quadrangle, pyramid_inference


def _remove_others_in_text(text_list):
    return [text.replace('[others]', '').replace('[others', '') for text in text_list]

def _remove_invalid_characters(text_list):
    return [re.sub(r'[^가-힣()a-zA-Z0-9-]+', '', text) for text in text_list]

def _order_points_clockwise(quad):
    quad_center = np.array([quad[:, 0].sum()/4, quad[:, 1].sum()/4])
    quad_norm = quad - quad_center
    atan_angle = np.arctan2(quad_norm[:,1], quad_norm[:,0])
    return quad[np.argsort(atan_angle)]

def _resize_quads(quads, prediction, mask_size=(28, 28)):
    assert len(quads) == len(prediction)
    quads = [q.astype(dtype=np.float32) for q in quads]
    bboxes = prediction.bbox.numpy().astype(dtype=np.int32)
    box_ws = (bboxes[:, 2] - bboxes[:, 0] - 1).astype(dtype=np.int32) / (mask_size[0] - 1)
    box_hs = (bboxes[:, 3] - bboxes[:, 1] - 1).astype(dtype=np.int32) / (mask_size[1] - 1)

    im_w, im_h = prediction.size
    new_quads = list()
    for quad, bbox, box_w, box_h in zip(quads, bboxes, box_ws, box_hs):
        new_quad = quad.copy()
        new_quad[:, 0] *= box_w
        new_quad[:, 1] *= box_h
        new_quad[:, 0] += bbox[0]
        new_quad[:, 1] += bbox[1]
        new_quad = np.round(new_quad)
        new_quads.append(new_quad)
    return [q.astype(dtype=np.int32) for q in new_quads]


def _get_intersect_over_y(source, target):
    x11, y11, x12, y12 = np.split(source, 4, axis=1)
    x21, y21, x22, y22 = np.split(target, 4, axis=1)
    dA = np.maximum(y11, np.transpose(y21))
    dB = np.minimum(y12, np.transpose(y22))
    hA = y12 - y11
    hB = y22 - y21
    intersect_y = np.maximum(dB-dA, 0)
    union_y = hA + hB - intersect_y
    return intersect_y / union_y

def _get_iou_y(s1, s2, divide_by_area1 = False, divide_by_area2 = False):
    '''
    s1 : [1 x 4]
    s2 : [n x 4]
    return: intersection_over_y : [1 x n]
    '''
    assert not (divide_by_area1 and divide_by_area2)
    x11, y11, x12, y12 = np.split(s1, 4, axis=1)
    x21, y21, x22, y22 = np.split(s2, 4, axis=1)
    
    dA = np.maximum(y11, np.transpose(y21))
    dB = np.minimum(y12, np.transpose(y22))
    intersection_y = np.maximum(dB - dA, 0)

    hA = y12 - y11
    hB = np.transpose(y22 - y21)

    if divide_by_area1:
        return intersection_y / hA

    if divide_by_area2:
        return intersection_y / hB

    return intersection_y / (hA + hB - intersection_y)

def _get_iou_x(s1, s2, divide_by_area1 = False, divide_by_area2 = False):
    '''
    s1 : [1 x 4]
    s2 : [n x 4]
    return: intersection_over_x : [1 x n]
    '''
    assert not (divide_by_area1 and divide_by_area2)
    x11, y11, x12, y12 = np.split(s1, 4, axis=1)
    x21, y21, x22, y22 = np.split(s2, 4, axis=1)
    
    dA = np.maximum(x11, np.transpose(x21))
    dB = np.minimum(x12, np.transpose(x22))
    intersection_x = np.maximum(dB - dA, 0)

    wA = x12 - x11
    wB = np.transpose(x22 - x21)

    if divide_by_area1:
        return intersection_x / wA

    if divide_by_area2:
        return intersection_x / wB

    return intersection_x / (wA + wB - intersection_x)

def _get_line_number(boxlist, iou_threshold=0.25, x_weight=0.75):
    line_index = 0
    lines = [None] * len(boxlist)

    if isinstance(boxlist.bbox, torch.Tensor):
        bbox = copy.deepcopy(boxlist.bbox.numpy())
    elif isinstance(boxlist.bbox, np.ndarray):
        bbox = copy.deepcopy(boxlist.bbox)
    iou_y = _get_intersect_over_y(bbox, bbox)
    # distacne_from_origin = np.roots(np.square(bbox[:,0]*x_weight)+np.square(bbox[:,1]), axis=0)
    distacne_from_origin = np.linalg.norm([bbox[:,0]*x_weight, bbox[:,1]], axis=0)
    max_distance = np.max(distacne_from_origin) + 1
    x_min = bbox[:,0]

    while lines.count(None) != 0:
        if line_index > 100:
            break
        no_line_index = np.array([True if line is None else False for line in lines])
        distacne_from_origin[~no_line_index] = max_distance
        top_instance_index = np.argmin(distacne_from_origin)
        lines[top_instance_index] = line_index
        no_line_index[top_instance_index] = False
        behind_top_index = x_min[top_instance_index] <= x_min
        iou_y_top = iou_y[top_instance_index]
        same_line_index = np.where((iou_y_top > iou_threshold) & behind_top_index)[0].tolist()
        while len(same_line_index) > 0:
            index = same_line_index.pop(0)
            if no_line_index[index]:
                lines[index] = line_index
                iou_y_top = iou_y[index]
                behind_top_index = x_min[index] < x_min
                sub_same_line_index = np.where((iou_y_top > iou_threshold) & behind_top_index)[0].tolist()
                same_line_index += list(set(sub_same_line_index) - set(same_line_index + [index]))
        line_index += 1
    
    unique_lines = list(set(lines))
    line_arr = np.array(lines)
    y_mean_list = []
    for line_index in unique_lines:
        line_indicies = line_arr==line_index
        y_mean = int(np.average(bbox[line_indicies][:,1::2]))
        y_mean_list.append(y_mean)
    
    new_line_arr = copy.deepcopy(line_arr)
    ordered_line_by_y_index = [i for _, i in sorted(zip(y_mean_list, unique_lines))]
    for i, line_index in enumerate(ordered_line_by_y_index):
        new_line_arr[line_arr==line_index] = i
    return new_line_arr


class BoxlistPostprocessor():
    # Collection of postprocessing functions that works on a single boxlist
    @staticmethod
    def filter_score(boxlist, score_threshold=0.3):
        valid_indices = boxlist.get_field('scores') > score_threshold
        return boxlist[valid_indices]

    @staticmethod
    def remove_overlapped_box(boxlist, iou_thresh=0.7):
        if len(boxlist) == 0:
            return boxlist
        ious = boxlist_iou(boxlist, boxlist, divide_by_area2=True).t()
        nested_index = np.array([False]*len(boxlist))
        for i, iou in enumerate(ious):
            iou[i] = -1.0
            if any(iou >= iou_thresh):
                nested_index[i] = True
        return boxlist[~nested_index]

    @staticmethod
    def get_overlapped_box(temp_box_list, pred_box_list, iou_thresh=0.7):
        if len(pred_box_list) == 0:
            return pred_box_list
        
        result_boxes = []
        for temp_box in temp_box_list:
            ious = boxlist_iou(temp_box, pred_box_list, divide_by_area2=True).t()
            nested_index = np.array([False]*len(pred_box_list))
            for i, iou in enumerate(ious):
                if any(iou >= iou_thresh):
                    nested_index[i] = True
            result_boxes.append(pred_box_list[nested_index])
        return result_boxes
        
    @staticmethod
    def remove_misclassified_box(boxlist, iou_thresh=0.85):
        if len(boxlist) == 0:
            return boxlist
        
        ious = boxlist_iou(boxlist, boxlist)
        misclassified_index = np.array([False] * len(boxlist))
        scores = boxlist.get_field('scores')
        for iou in ious:
            overlapped_indices = torch.where(iou >= iou_thresh)[0]
            if len(overlapped_indices) == 1:
                continue
            
            overlapped_scores = scores[overlapped_indices]
            correct_index = overlapped_indices[torch.argmax(overlapped_scores)]

            for overlapped_index in overlapped_indices:
                if overlapped_index == correct_index:
                    continue
                misclassified_index[overlapped_index] = True

        return boxlist[~misclassified_index]

    @staticmethod
    def sort_quads_clockwise(boxlist):
        quads = boxlist.get_field('quads')
        if isinstance(quads, np.ndarray):
            sorted_quads = np.zeros_like(quads)
        elif isinstance(quads, torch.Tensor):
            sorted_quads = torch.zeros_like(quads)
        for _i, quad in enumerate(quads):
            sorted_quads[_i] = _order_points_clockwise(quad)
        boxlist.add_field('quads', sorted_quads)
        return boxlist

    @staticmethod
    def sort_from_left(boxlist):
        index_from_left_to_right = np.argsort(boxlist.bbox[:, 0])
        return boxlist[index_from_left_to_right]

    @staticmethod
    def get_text_lines(boxlist):
        lines = _get_line_number(boxlist)
        boxlist.add_field('lines', lines)
        return boxlist

    @staticmethod
    def sort_tblr(boxlist):
        lines = _get_line_number(boxlist)
        sorted_boxlist = BoxlistPostprocessor.sort_from_left(boxlist[lines==0])

        if len(np.unique(lines)) == 1:
            return sorted_boxlist

        for line in list(set(lines) - {0}):
            line_boxlist = BoxlistPostprocessor.sort_from_left(boxlist[lines==line])
            sorted_boxlist = sorted_boxlist.merge_other_boxlist(line_boxlist)
        return sorted_boxlist

    @staticmethod
    def decode_text(boxlist, converter, remove_others=False):
        """decode texts from e2e prediction"""
        text_tensors = boxlist.get_field('trans')
        batch_max_length = torch.IntTensor([text_tensors[0].shape[0]] * len(text_tensors))
        decoded_texts = converter.decode(torch.stack(text_tensors), batch_max_length)
        decoded_texts = [trans[:trans.find('[s]')] for trans in decoded_texts]
        if remove_others:
            decoded_texts = _remove_others_in_text(decoded_texts)
        boxlist.add_field('texts', decoded_texts)
        return boxlist

    @staticmethod
    def decode_text_rec(boxlist, converter, remove_others=False):
        """decode texts from prediction of recognition model"""
        text_tensors = boxlist.get_field('pred').unsqueeze(0).type(torch.int32)
        decoded_texts = converter.decode(text_tensors, torch.tensor([text_tensors.shape[1]]))
        decoded_texts = [trans[:trans.find('[s]')] for trans in decoded_texts]
        if remove_others:
            decoded_texts = _remove_others_in_text(decoded_texts)
        boxlist.add_field('texts', decoded_texts)
        return boxlist

    @staticmethod
    def filter_text(boxlist):
        text_list = boxlist.get_field('trans')
        text_list = _remove_others_in_text(text_list)
        text_list = _remove_invalid_characters(text_list)
        valid_text_indices = np.array(text_list, dtype=np.bool)
        return boxlist[valid_text_indices]

    @staticmethod
    def filter_invalid_polygons(boxlist):
        quads = boxlist.get_field('quads')
        polygons = [Polygon([(x.item(), y.item()) for x, y in zip(q[:,0], q[:,1])]) for q in quads]
        boxlist.add_field('polygons', polygons)

        poly_valid = [_.is_valid for _ in polygons]
        return boxlist[np.array(poly_valid, dtype=bool)]

    @staticmethod
    def filter_spatially_unrelated_boxes(boxlist, horizontally=True, vertically=True, distance_factor=2.5):
        assert horizontally or vertically
        bbox = boxlist.convert('xyxy').bbox.clone()
        bbox_centers = torch.stack([(bbox[:,2] + bbox[:,0])/2, (bbox[:,3] + bbox[:,1])/2], dim=1)
        base_box_index = int(boxlist.get_field('scores').argmax())
        base_box_center = bbox_centers[base_box_index]
        w = bbox[base_box_index, 2] - bbox[base_box_index, 0]
        h = bbox[base_box_index, 3] - bbox[base_box_index, 1]
        max_distance = torch.stack([w, h]).abs() * distance_factor

        inds_to_discard = torch.tensor([False]*len(boxlist))
        for i, _center in enumerate(bbox_centers):
            if i == base_box_index:
                continue
            distance = torch.abs(_center - base_box_center)
            if horizontally and vertically:
                inds_to_discard[i] = any(distance > max_distance)
            elif horizontally:
                inds_to_discard[i] = distance[0] > max_distance[0]
            elif vertically:
                inds_to_discard[i] = distance[1] > max_distance[1]
        return boxlist[~inds_to_discard]


class BatchPostprocessor():
    @staticmethod
    def resize_predictions(predictions, dataset, remove_small=True, remove_size_threshold=10, dpi_resample=False):
        result = []
        for image_id, prediction in enumerate(predictions):
            if dpi_resample:
                img = dataset.get_pil_image(image_id)
                resampled_size, _ = dataset._get_dpi_resampled_size(img)
                prediction_orig_size = prediction.resize(resampled_size)
            else:
                img_info = dataset.get_img_info(image_id)
                image_width = img_info["width"]
                image_height = img_info["height"]
                prediction_orig_size = prediction.resize((image_width, image_height))
            if remove_small:
                prediction = remove_small_boxes(prediction_orig_size, min_size=10)
            else:
                prediction = prediction_orig_size
            result.append(prediction)
        return result

    @staticmethod
    def mask_to_quadrangle(predictions, use_pyramid_mask=False, force_rect=False, with_masker=True, allow_polygon=False):
        masker_thres = 0.001 if use_pyramid_mask else 0.5
        if with_masker:
            masker = Masker(masker_thres, 1)

        result = []
        for image_id, prediction in tqdm(enumerate(predictions), total=len(predictions)):
            if not prediction.has_field('mask') or prediction.has_field('quads'):
                result.append(prediction)
                continue

            masks = prediction.get_field('mask')
            if not use_pyramid_mask:
                if with_masker:
                    masks = masker([masks], [prediction])[0] # n x 1 x img_h x img_w tensor
                    masks = masks.squeeze(1)
                else:
                    masks = masks.squeeze(1)
                    masks = masks.float() > masker_thres
                quads = [mask_to_quadrangle(m, force_rect=force_rect, allow_polygon=allow_polygon) for m in masks]
                if not with_masker and len(quads) > 0:
                    quads = _resize_quads(quads, prediction, mask_size = masks.shape[-2:])
                if not allow_polygon:
                    quads = torch.tensor(quads, dtype=torch.int32)
                prediction.add_field('quads', quads)
            else:
                # masks = masker([masks], [prediction])[0] # n x 1 x img_h x img_w tensor
                mask_resolution = tuple(masks.shape[-2:])
                mode = prediction.mode
                pyramid_processor = pyramid_inference(mask_resolution, mode)
                quad_list = []
                masks = masks.to(torch.float32)
                masks = torch.log(masks / (1 - masks)) # inverse sigmoid
                masks.clamp_(0.0, 1.0)
                for mask_prob, bb in zip(masks, prediction.bbox):
                    quad, is_err = pyramid_processor(mask_prob, bb)
                    if is_err:
                        # TODO: thresholding + minAreaRect
                        bb = bb.tolist()
                        if prediction.mode == "xyxy":
                            quad = [[bb[i], bb[j]] for i,j in zip([0, 2, 2, 0],[1, 1, 3, 3])]
                        elif prediction.mode == "xywh":
                            quad = [
                                [bb[0], bb[1]], [bb[0]+bb[2], bb[1]],
                                [bb[0]+bb[2], bb[1]+bb[3]], [bb[0], bb[1]+bb[3]]
                            ]
                    quad_list.append(quad)
                quads = torch.tensor(quad_list, dtype=torch.int32)
                prediction.add_field("quads", quads)
            result.append(prediction)
        return result

    @staticmethod
    def decode_texts(predictions, converter):
        return [BoxlistPostprocessor.decode_text(pred, converter) for pred in predictions]

    @staticmethod
    def decode_texts_rec(predictions, converter):
        return [BoxlistPostprocessor.decode_text_rec(pred, converter) for pred in predictions]

    @staticmethod
    def remove_invalid_polygons(predictions):
        return [BoxlistPostprocessor.filter_invalid_polygons(pred) for pred in predictions]
