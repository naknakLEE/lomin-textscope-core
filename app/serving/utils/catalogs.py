import json
import os
from lovit.structures.catalogs import LabelCatalog, DocumentCatalog


class ELabelCatalog(LabelCatalog):
    @staticmethod
    def get(label_files, data_dir=None, decipher=None):
        if data_dir is None:
            data_dir = LabelCatalog.LABEL_DIR
        characters = ""
        for label_file in label_files:
            if decipher:
                label_path = os.path.join(
                    data_dir, decipher.prefix + LabelCatalog.LABELS[label_file]
                )
                assert os.path.exists(label_path), label_path
                label = decipher(label_path)
                characters += "".join(label).replace("\n", "").replace("\r", "")
            else:
                label_path = os.path.join(data_dir, LabelCatalog.LABELS[label_file])
                assert os.path.exists(label_path)
                label = open(label_path, encoding="utf-8").readlines()
                characters += "".join(label).replace("\n", "")
        return characters


class EDocumentCatalog(DocumentCatalog):
    @classmethod
    def get_template(cls, doc_name, decipher=None):
        if decipher:
            path = os.path.join(cls.BASE_DIR, decipher.prefix + cls.MAP[doc_name]["template"])
            return decipher(path)

        with open(cls.get_template_path(doc_name)) as f:
            return json.load(f)
