import numpy as np
import onnxruntime as rt
import os

from PIL import Image
from service_streamer import ThreadedStreamer

from serving.idcard_utils.utils import build_preprocess


class BaseStreamer(object):
    def __init__(self, infer_sess_map, service_cfg):
        self.orb_matcher = dict()
        self.infer_sess_map = infer_sess_map
        self.service_cfg = service_cfg
        self.decipher = False
        self._load_models()
        self.is_available = True

    def _load_models(self):       
        resources = self.service_cfg['resources']
        for resource in resources:
            _type = resource['type']
            _name = resource['name']
            _use_streamer = resource['use_streamer'] if 'use_streamer' in resource else False
            _model_path = resource['model_path'] if 'model_path' in resource else ''
            _batch_size = resource['batch_size'] if 'batch_size' in resource else 1
            _max_latency = resource['max_latency'] if 'max_latency' in resource else 0.1
            _preprocess_cfg = resource['preprocess'] if 'preprocess' in resource else []
            _extra_config = resource['config'] if 'config' in resource else {}
            if _name in self.infer_sess_map:
                continue
            
            if _type == "onnx_model":
                _model_name = os.path.basename(_model_path)
                # if self.decipher:
                #     dir_path, basename = os.path.split(_model_path)
                #     _model_path = os.path.join(dir_path, self.decipher.prefix + basename)
                #     _onnx_io = self.decipher(_model_path)
                #     _sess = rt.InferenceSession(_onnx_io.getvalue())
                # else:
                #     _sess = rt.InferenceSession(_model_path)
                _sess = rt.InferenceSession(_model_path)

                output_names = [_.name for _ in _sess.get_outputs()]

                def batch_prediction(inputs):
                    images = np.stack(inputs)
                    outputs = _sess.run(output_names, {'images': images})
                    batch_size = len(images)
                    output_list = list()
                    for i in range(batch_size):
                        _output = list()
                        for j in range(len(output_names)):
                            _output.append(outputs[j][i])
                        output_list.append(_output)
                    return output_list

                _pre_process = build_preprocess(_preprocess_cfg)

                if 'label_classes' in _extra_config:
                    lookup_table = np.asarray(_extra_config['label_classes'])
                    _extra_config['label_classes'] = lookup_table
                if _use_streamer:
                    streamer = ThreadedStreamer(
                        batch_prediction,
                        batch_size=_batch_size,
                        max_latency=_max_latency
                    )
                else:
                    streamer = None
                self.infer_sess_map[_name] = {
                    'streamer': streamer,
                    'sess': _sess,
                    'output_names': output_names,
                    'preprocess': _pre_process,
                    'config': _extra_config,
                    'batch_size': _batch_size
                }
            elif _type == 'orb_matcher':
                assert 'config' in resource
                assert 'image_path' in resource['config'] and len(resource['config']['image_path']) > 0
                _image_path = resource['config']['image_path']
                self.orb_matcher['image_path'] = _image_path
            else:
                raise ValueError
    
    def check_status(self):
        try:
            self._load_models()
            return {
                'is_available': True,
                'message': "Successfully re-load session",
            }
        except:
            pass
        return {
            'is_available': False,
            'message': "Failed to re-load session",
        }


    def __call__(self, image: Image) -> dict:
        result = dict()
        raise NotImplementedError
        return result