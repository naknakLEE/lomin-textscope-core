import re
import copy
import torch
import numpy as np

from soynlp.hangle import jamo_levenshtein
from maskrcnn_benchmark.structures.keyvalue_dict import KVDict
from maskrcnn_benchmark.data.datasets.postprocess.commons import _get_iou_y, BoxlistPostprocessor as PP

ESTATE_NUM_KEYWORD = '부동산고유번호'
SERIAL_NUM_KEYWORD = '일련번호'
UPPER_BOUNDARY_KEYWORDS = ['비밀번호', '일련번호', '등기원인및일자']

def get_keyword_index(preds, KEYWORD, priority = 'upper'):
    '''
    priority : upper / bottom / right / left
    '''
    texts = preds.get_field('texts')
    edit_distances = [jamo_levenshtein(text, KEYWORD) for text in texts]
    min_indices = np.where(edit_distances == np.min(edit_distances))[0]
    if len(min_indices) == 1:
        return min_indices[0]

    keyword_bboxes = preds.bbox[min_indices]
    if priority == 'upper':
        index = min_indices[np.argmin(keyword_bboxes[:, 1])]
    
    elif priority == 'bottom':
        index = min_indices[np.argmax(keyword_bboxes[:, 3])]

    elif priority == 'left':
        index = min_indices[np.argmin(keyword_bboxes[:, 0])]

    elif priority == 'right':
        index = min_indices[np.argmax(keyword_bboxes[:, 2])]

    return index

def get_regex_index(preds, exp, priority = 'bottom'):
    '''
    priority : upper / bottom / right / left
    If there is no text satisfied expression, 
    Return None
    '''
    texts = preds.get_field('texts')
    regex_mask = np.array([True if re.search(exp, text) else False for text in texts])
    
    mask_indices = np.where(regex_mask == True)[0]
    if len(mask_indices) == 0:
        return None

    mask_bboxes = preds.bbox[mask_indices]
    if priority == 'upper':
        index = mask_indices[np.argmin(mask_bboxes[:, 1])]
    
    elif priority == 'bottom':
        index = mask_indices[np.argmax(mask_bboxes[:, 3])]

    elif priority == 'left':
        index = mask_indices[np.argmin(mask_bboxes[:, 0])]

    elif priority == 'right':
        index = mask_indices[np.argmax(mask_bboxes[:, 2])]
    
    else:
        raise
    
    return index

def fix_password(pwd_preds):
    return None


def get_estate_num(preds):
    try:
        texts = np.array(preds.get_field('texts'))
        text_filter = np.array([True if re.search('\d{4}-\d{4}-\d{6}', text) else False for text in texts])

        estate_num = ''
        keyword_index = get_keyword_index(preds, ESTATE_NUM_KEYWORD, priority = 'upper')
        y_iou_score = _get_iou_y(preds.bbox[np.array([keyword_index])], preds.bbox)[0]
        
        y_iou_score[keyword_index] = 0
        filter_mask = (y_iou_score > 0) * (text_filter)
        
        if np.sum(filter_mask) == 0:
            text_filter = np.array([True if re.search('\d{4}-', text) else False for text in texts])
            filter_mask = (y_iou_score > 0) * (text_filter)
        
        if np.sum(filter_mask) == 0:
            filter_mask = np.array([True if re.search('\d{4}-\d{4}-\d{6}', text) else False for text in texts])
        
        if np.sum(filter_mask) == 0:
            filter_mask = np.array([True if re.search('\d{4}-\d{1}', text) else False for text in texts])

        candidates = preds[torch.tensor(filter_mask, dtype = torch.bool)]
        
        if len(candidates) > 0:
            candidates_text = candidates.get_field('texts')
            max_idx = np.argmax(y_iou_score[filter_mask])
            estate_num = candidates_text[max_idx]
    
    except:
        estate_num = ''
        texts = np.array(preds.get_field('texts'))
        text_filter = np.array([True if re.search('\d{4}-\d{4}-\d{6}', text) else False for text in texts])
        candidates = preds[torch.tensor(text_filter, dtype = torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field('texts')
            estate_num = candidates_text[0]

    return estate_num

def get_serial_num(preds):
    try:
        texts = np.array(preds.get_field('texts'))
        text_filter = np.array([True if re.search('[A-Z]{4}-[A-Z]{4}-[A-Z]{4}', text) else False for text in texts])

        serial_num = ''
        keyword_index = get_keyword_index(preds, SERIAL_NUM_KEYWORD, priority = 'upper')
        y_iou_score = _get_iou_y(preds.bbox[np.array([keyword_index])], preds.bbox)[0]

        y_iou_score[keyword_index] = 0
        filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            text_filter = np.array([True if re.search('[A-Z]{4}', text) else False for text in texts])
            filter_mask = (y_iou_score > 0) * (text_filter)
        
        if np.sum(filter_mask) == 0:
            filter_mask = np.array([True if re.search('[A-Z]{4}-[A-Z]{4}-[A-Z]{4}', text) else False for text in texts])

        if np.sum(filter_mask) == 0:
            filter_mask = np.array([True if re.search('[A-Z]{4}', text) else False for text in texts])

        candidates = preds[torch.tensor(filter_mask, dtype = torch.bool)]
        
        if len(candidates) > 0:
            candidates_text = candidates.get_field('texts')
            max_idx = np.argmax(y_iou_score[filter_mask])
            serial_num = candidates_text[max_idx]
    
    except:
        serial_num = ''
        texts = np.array(preds.get_field('texts'))
        text_filter = np.array([True if re.search('[A-Z]{4}-[A-Z]{4}-[A-Z]{4}', text) else False for text in texts])
        candidates = preds[torch.tensor(text_filter, dtype = torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field('texts')
            serial_num = candidates_text[0]

    return serial_num

def get_indices(texts, KEYWORDS):
    indices = list()
    for keyword in KEYWORDS:
        edit_distances = [jamo_levenshtein(text, keyword) for text in texts]
        min_idx = np.argmin(edit_distances)
        indices.append(min_idx)

    return indices

def get_upper_boundary(texts, preds):
    upper_indices = [get_keyword_index(preds, KEYWORD, priority = 'upper') for KEYWORD in UPPER_BOUNDARY_KEYWORDS]
    upper_boundary = [preds.bbox[index, 1] for index in upper_indices]
    upper_boundary = sorted(upper_boundary, reverse = True)
    
    return upper_boundary


def get_bottom_boundary(preds):
    year_idx = get_regex_index(preds, '\d{4}년', priority = 'bottom')
    month_idx = get_regex_index(preds, '\d{1, 2}월', priority = 'bottom')
    day_idx = get_regex_index(preds, '\d{1, 2}일', priority = 'bottom')

    year = preds.bbox[year_idx, 3] if year_idx is not None else 0
    month = preds.bbox[month_idx, 3] if month_idx is not None else 0
    day = preds.bbox[day_idx, 3] if day_idx is not None else 0

    date_boundary = max([year, month, day])

    less_tighter_index = get_keyword_index(preds, '등기관', priority = 'bottom')
    less_tighter_boundary = preds.bbox[less_tighter_index, 3]
    lower_boundary = sorted([date_boundary, less_tighter_boundary])
    
    return lower_boundary
    

def get_passwords(preds):
    pwd_candidates = preds.copy_with_fields(list(preds.extra_fields.keys()), skip_missing = False)
    texts = pwd_candidates.get_field('texts')
    text_filter = np.array([True if re.match('\d{2}-\d{4}', text) else False for text in texts])
    pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype = torch.bool)]
    try:
        pwd_numbers = min(50, np.sum(text_filter))
        upper_boundaries = get_upper_boundary(texts, preds)
        
        for upper_boundary in upper_boundaries:
            _pwd_candidates = pwd_candidates[torch.tensor(pwd_candidates.bbox[:, 3] > upper_boundary, dtype = torch.bool)]
            if len(_pwd_candidates) == pwd_numbers:
                continue
        
        '''
        if len(_pwd_candidates) > 50 :
            filtered_pwd_candidates = _pwd_candidates
            bottom_boundaries = get_bottom_boundary(preds)

            for bottom_boundary in bottom_boundaries:
                _filtered_pwd_candidates = filtered_pwd_candidates[torch.tensor(filtered_pwd_candidates.bbox[:, 1] < bottom_boundary, dtype = torch.bool)]
                if len(_filtered_pwd_candidates) == pwd_numbers:
                    continue
        
            _pwd_candidates = _filtered_pwd_candidates
        '''
        pwd_mask = (preds.bbox[:, 1] > int(min(_pwd_candidates.bbox[:, 1] - 1))) * (preds.bbox[:, 3] < int(max(_pwd_candidates.bbox[:, 3] + 1)))
        passwords = preds[torch.tensor(pwd_mask, dtype = torch.bool)]
        password_texts = passwords.get_field('texts')
        #passwords = fix_password(passwords)

    except:
        pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype = torch.bool)]
        password_texts = pwd_candidates.get_field('texts')

    return password_texts


def postprocess_regi_cert(predictions, *args):
    predictions = PP.sort_tblr(predictions)
    if isinstance(predictions.bbox, torch.Tensor):
        predictions.bbox = copy.deepcopy(predictions.bbox.numpy())
    
    estate_num = get_estate_num(predictions)
    serial_num = get_serial_num(predictions)
    pwd_texts = get_passwords(predictions)

    result = {}
    result.update({'estate_num' : estate_num})
    result.update({'serial_num' : serial_num})
    result.update({'passwords' : pwd_texts})
    
    result_all_classes = {}

    for k,v in result.items():
        result_all_classes[k + '_value'] = v

    return KVDict(result_all_classes, str), {}