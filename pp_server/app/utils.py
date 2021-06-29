import PIL
from PIL import Image
import numpy as np
import cv2
import torch
import copy

from shapely.geometry import Polygon


def mask_to_quadrangle(mask, mask_convex_hull=False, force_rect=False, allow_polygon=False):
    assert isinstance(mask, torch.Tensor)
    assert mask.ndimension() == 2
    assert mask.dtype == torch.bool
    mask = mask.numpy().astype(np.uint8)

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # TODO: handle this
    # assert len(contours) > 0
    if len(contours) == 0:
        return np.zeros((4, 2), dtype=np.int32)

    if not mask_convex_hull:
        areas = np.array([cv2.contourArea(cnt) for cnt in contours])
        idx_max_area = np.argsort(areas)[-1]
        contour = contours[idx_max_area]
    else:
        contour = np.concatenate(contours, 0)
        contour = cv2.convexHull(contour, False)
        mask = cv2.fillConvexPoly(np.zeros(mask.shape), contour, 1)
        mask = np.uint8(mask)

    if force_rect:
        marect = cv2.minAreaRect(contour)
        quad = cv2.boxPoints(marect)
        return np.int32(quad)

    epsilon = 0.02 * cv2.arcLength(contour, True)
    eps_min = 0.0
    eps_max = epsilon
    eps = (eps_max + eps_min) / 2

    # find upperbound
    approx = cv2.approxPolyDP(contour, eps, True)
    cnt = 0

    if allow_polygon:
        return approx.squeeze(1)

    while len(approx) < 4 and cnt < 10:
        eps_max = (eps_max - eps_min) * 2 + eps_max
        eps_min = eps
        eps = (eps_max + eps_min) / 2 
        approx = cv2.approxPolyDP(contour, eps, True)
        cnt += 1

    # find possible quadrangle approximation
    if len(approx) != 4:
        for j in range(10):
            approx = cv2.approxPolyDP(contour, eps, True)  
            if len(approx) == 4:
                break    
            if len(approx) < 4: # reduce eps
                eps_max = eps
            else: # increase eps
                eps_min = eps
            eps = (eps_max + eps_min) / 2

    # get rotatedRect
    marect = cv2.minAreaRect(contour)
    marect = cv2.boxPoints(marect)

    approx = np.squeeze(approx)
    contour = np.squeeze(contour)

    if len(approx) != 4:
        quad = marect 
    else:
        poly_marect = Polygon([(x, y) for x, y in zip(marect[:, 0], marect[:, 1])])
        poly_approx = Polygon([(x, y) for x, y in zip(approx[:, 0], approx[:, 1])])
        poly_contour = Polygon([(x, y) for x, y in zip(contour[:, 0], contour[:, 1])])

        if not poly_marect.is_valid or \
            not poly_approx.is_valid or \
            not poly_contour.is_valid:
            quad = marect
        else:
            inter_marect = poly_marect.intersection(poly_contour).area
            inter_approx = poly_approx.intersection(poly_contour).area
            union_marect = poly_marect.union(poly_contour).area
            union_approx = poly_approx.union(poly_contour).area

            iou_marect = inter_marect / union_marect
            iou_approx = inter_approx / union_approx
            if iou_marect > iou_approx:
                quad = marect 
            else:
                quad = np.squeeze(approx)

    return np.int32(quad)
