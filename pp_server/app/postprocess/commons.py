import re
import copy
import torch
import numpy as np
from shapely.geometry import Polygon


# implementation from https://github.com/kuangliu/torchcv/blob/master/torchcv/utils/box.py
# with slight modifications
def boxlist_iou(boxlist1, boxlist2, divide_by_area2=False, return_all=False):
    """Compute the intersection over union of two set of boxes.
    The box order must be (xmin, ymin, xmax, ymax).
    Arguments:
      box1: (BoxList) bounding boxes, sized [N,4].
      box2: (BoxList) bounding boxes, sized [M,4].
      devide_by_area2: (bool) divide by area2, instead of union.
    Returns:
      (tensor) iou, sized [N,M].
    Reference:
      https://github.com/chainer/chainercv/blob/master/chainercv/utils/bbox/bbox_iou.py
    """
    # assert all(
    #     x != y for x, y in zip(boxlist1.size, boxlist2.size)
    # ), "boxlists should have same image size, got {}, {}".format(
    #     boxlist1, boxlist2
    # )
    # if boxlist1.size != boxlist2.size:
    #     raise RuntimeError(
    #         "boxlists should have same image size, got {}, {}".format(boxlist1, boxlist2)
    #     )
    boxlist1 = boxlist1.convert("xyxy")
    boxlist2 = boxlist2.convert("xyxy")
    N = len(boxlist1)
    M = len(boxlist2)
    box1, box2 = boxlist1.bbox, boxlist2.bbox
    if isinstance(box1, np.ndarray):
        box1 = torch.tensor(box1, dtype=torch.float32)
    if isinstance(box2, np.ndarray):
        box2 = torch.tensor(box2, dtype=torch.float32)
    iou = torch.zeros([N, M], dtype=torch.float32).to(box1.device)
    if return_all:
        inter = torch.zeros([N, M], dtype=torch.float32).to(box1.device)
    TO_REMOVE = 1
    if N < M:
        area2 = boxlist2.area()
        for i in range(0, N, 20):
            b = box1[i : min(i + 20, N)]
            area1 = (b[:, 2] - b[:, 0] + TO_REMOVE) * (b[:, 3] - b[:, 1] + TO_REMOVE)
            i_inter = (
                (
                    torch.min(b[:, None, 2:], box2[:, 2:])
                    - torch.max(b[:, None, :2], box2[:, :2])  # rb  # lt
                    + TO_REMOVE
                )
                .clamp_(min=0)
                .prod(dim=2)
            )
            if return_all:
                inter[i : min(i + 20, N), :] = i_inter
            if divide_by_area2:
                iou[i : min(i + 20, N), :] = i_inter / area2
            else:
                iou[i : min(i + 20, N), :] = torch.where(
                    i_inter > 0,
                    i_inter / (area1[:, None] + area2 - i_inter),
                    torch.zeros(1, dtype=i_inter.dtype, device=i_inter.device),
                )
    else:
        area1 = boxlist1.area()
        for j in range(0, M, 20):
            b = box2[j : min(j + 20, M)]
            area2 = (b[:, 2] - b[:, 0] + TO_REMOVE) * (b[:, 3] - b[:, 1] + TO_REMOVE)
            j_inter = (
                (
                    torch.min(box1[:, None, 2:], b[:, 2:])
                    - torch.max(box1[:, None, :2], b[:, :2])  # rb  # lt
                    + TO_REMOVE
                )
                .clamp_(min=0)
                .prod(dim=2)
            )
            if return_all:
                inter[:, j : min(j + 20, N)] = j_inter
            if divide_by_area2:
                iou[:, j : min(j + 20, M)] = j_inter / area2
            else:
                iou[:, j : min(j + 20, M)] = torch.where(
                    j_inter > 0,
                    j_inter / (area1[:, None] + area2 - j_inter),
                    torch.zeros(1, dtype=j_inter.dtype, device=j_inter.device),
                )
    if return_all:
        return iou, inter
    return iou


def _remove_others_in_text(text_list):
    return [text.replace("[others]", "").replace("[others", "") for text in text_list]


def _remove_invalid_characters(text_list):
    return [re.sub(r"[^가-힣()a-zA-Z0-9-]+", "", text) for text in text_list]


def _order_points_clockwise(quad):
    quad_center = np.array([quad[:, 0].sum() / 4, quad[:, 1].sum() / 4])
    quad_norm = quad - quad_center
    atan_angle = np.arctan2(quad_norm[:, 1], quad_norm[:, 0])
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
    intersect_y = np.maximum(dB - dA, 0)
    union_y = hA + hB - intersect_y
    return intersect_y / union_y


def _get_iou_y(s1, s2, divide_by_area1=False, divide_by_area2=False):
    """
    s1 : [1 x 4]
    s2 : [n x 4]
    return: intersection_over_y : [1 x n]
    """
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


def _get_iou_x(s1, s2, divide_by_area1=False, divide_by_area2=False):
    """
    s1 : [1 x 4]
    s2 : [n x 4]
    return: intersection_over_x : [1 x n]
    """
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
    distacne_from_origin = np.linalg.norm([bbox[:, 0] * x_weight, bbox[:, 1]], axis=0)
    max_distance = np.max(distacne_from_origin) + 1
    x_min = bbox[:, 0]

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
                sub_same_line_index = np.where((iou_y_top > iou_threshold) & behind_top_index)[
                    0
                ].tolist()
                same_line_index += list(set(sub_same_line_index) - set(same_line_index + [index]))
        line_index += 1

    unique_lines = list(set(lines))
    line_arr = np.array(lines)
    y_mean_list = []
    for line_index in unique_lines:
        line_indicies = line_arr == line_index
        y_mean = int(np.average(bbox[line_indicies][:, 1::2]))
        y_mean_list.append(y_mean)

    new_line_arr = copy.deepcopy(line_arr)
    ordered_line_by_y_index = [i for _, i in sorted(zip(y_mean_list, unique_lines))]
    for i, line_index in enumerate(ordered_line_by_y_index):
        new_line_arr[line_arr == line_index] = i
    return new_line_arr


class BoxlistPostprocessor:
    # Collection of postprocessing functions that works on a single boxlist
    @staticmethod
    def filter_score(boxlist, score_threshold=0.3):
        valid_indices = boxlist.get_field("scores") > score_threshold
        return boxlist[valid_indices]

    @staticmethod
    def remove_overlapped_box(boxlist, iou_thresh=0.7):
        if len(boxlist) == 0:
            return boxlist
        ious = boxlist_iou(boxlist, boxlist, divide_by_area2=True).t()
        nested_index = np.array([False] * len(boxlist))
        for i, iou in enumerate(ious):
            iou[i] = -1.0
            if any(iou >= iou_thresh):
                nested_index[i] = True
        print(f"nested_index: {len(boxlist)}")
        # print(f"bbox.add_field(k, v[item_np]): {len(v)}")

        return boxlist[~nested_index]

    @staticmethod
    def get_overlapped_box(temp_box_list, pred_box_list, iou_thresh=0.7):
        if len(pred_box_list) == 0:
            return pred_box_list

        result_boxes = []
        for temp_box in temp_box_list:
            ious = boxlist_iou(temp_box, pred_box_list, divide_by_area2=True).t()
            nested_index = np.array([False] * len(pred_box_list))
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
        scores = boxlist.get_field("scores")
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
        quads = boxlist.get_field("quads")
        if isinstance(quads, np.ndarray):
            sorted_quads = np.zeros_like(quads)
        elif isinstance(quads, torch.Tensor):
            sorted_quads = torch.zeros_like(quads)
        for _i, quad in enumerate(quads):
            sorted_quads[_i] = _order_points_clockwise(quad)
        boxlist.add_field("quads", sorted_quads)
        return boxlist

    @staticmethod
    def sort_from_left(boxlist):
        index_from_left_to_right = np.argsort(boxlist.bbox[:, 0])
        return boxlist[index_from_left_to_right]

    @staticmethod
    def get_text_lines(boxlist):
        lines = _get_line_number(boxlist)
        boxlist.add_field("lines", lines)
        return boxlist

    @staticmethod
    def sort_tblr(boxlist):
        lines = _get_line_number(boxlist)
        sorted_boxlist = BoxlistPostprocessor.sort_from_left(boxlist[lines == 0])

        if len(np.unique(lines)) == 1:
            return sorted_boxlist

        for line in list(set(lines) - {0}):
            line_boxlist = BoxlistPostprocessor.sort_from_left(boxlist[lines == line])
            sorted_boxlist = sorted_boxlist.merge_other_boxlist(line_boxlist)
        return sorted_boxlist

    @staticmethod
    def decode_text(boxlist, converter, remove_others=False):
        """decode texts from e2e prediction"""
        text_tensors = boxlist.get_field("trans")
        batch_max_length = torch.IntTensor([text_tensors[0].shape[0]] * len(text_tensors))
        decoded_texts = converter.decode(torch.stack(text_tensors), batch_max_length)
        decoded_texts = [trans[: trans.find("[s]")] for trans in decoded_texts]
        if remove_others:
            decoded_texts = _remove_others_in_text(decoded_texts)
        boxlist.add_field("texts", decoded_texts)
        return boxlist

    @staticmethod
    def decode_text_rec(boxlist, converter, remove_others=False):
        """decode texts from prediction of recognition model"""
        text_tensors = boxlist.get_field("pred").unsqueeze(0).type(torch.int32)
        decoded_texts = converter.decode(text_tensors, torch.tensor([text_tensors.shape[1]]))
        decoded_texts = [trans[: trans.find("[s]")] for trans in decoded_texts]
        if remove_others:
            decoded_texts = _remove_others_in_text(decoded_texts)
        boxlist.add_field("texts", decoded_texts)
        return boxlist

    @staticmethod
    def filter_text(boxlist):
        text_list = boxlist.get_field("trans")
        text_list = _remove_others_in_text(text_list)
        text_list = _remove_invalid_characters(text_list)
        valid_text_indices = np.array(text_list, dtype=np.bool)
        return boxlist[valid_text_indices]

    @staticmethod
    def filter_invalid_polygons(boxlist):
        quads = boxlist.get_field("quads")
        polygons = [
            Polygon([(x.item(), y.item()) for x, y in zip(q[:, 0], q[:, 1])]) for q in quads
        ]
        boxlist.add_field("polygons", polygons)

        poly_valid = [_.is_valid for _ in polygons]
        return boxlist[np.array(poly_valid, dtype=bool)]

    @staticmethod
    def filter_spatially_unrelated_boxes(
        boxlist, horizontally=True, vertically=True, distance_factor=2.5
    ):
        assert horizontally or vertically
        bbox = boxlist.convert("xyxy").bbox.clone()
        bbox_centers = torch.stack(
            [(bbox[:, 2] + bbox[:, 0]) / 2, (bbox[:, 3] + bbox[:, 1]) / 2], dim=1
        )
        base_box_index = int(boxlist.get_field("scores").argmax())
        base_box_center = bbox_centers[base_box_index]
        w = bbox[base_box_index, 2] - bbox[base_box_index, 0]
        h = bbox[base_box_index, 3] - bbox[base_box_index, 1]
        max_distance = torch.stack([w, h]).abs() * distance_factor

        inds_to_discard = torch.tensor([False] * len(boxlist))
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
