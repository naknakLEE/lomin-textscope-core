import re
import numpy as np
from collections import defaultdict

class PostprocessResult():
    def __init__(self, pptype, **_):
        assert pptype in ['kv', 'idcard']
        self.pptype = pptype


class KVDict(PostprocessResult):
    def __init__(self, result_all_classes, default_type, **_):
        PostprocessResult.__init__(self, pptype='kv', **_)
        self.keys = defaultdict(default_type)
        self.values = defaultdict(default_type)
        self.keys.update({
            re.sub('_key$', '', k): v \
                for k, v in result_all_classes.items() \
                    if k.endswith('_key')
        })
        self.values.update({
            re.sub('_value$', '', k): v \
                for k, v in result_all_classes.items() \
                    if k.endswith('_value')
        })

class ValDict(PostprocessResult):
    def __init__(self, result_all_classes, default_type, **_):
        PostprocessResult.__init__(self, pptype='kv', **_)
        self.values = defaultdict(default_type)
        self.values.update(result_all_classes)