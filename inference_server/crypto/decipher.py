import re
import os
import crypto.solver as solver


class Decipher:
    def __init__(self, key="", prefix="lo_"):
        super().__init__()
        self.key = key
        self.prefix = prefix

        image_target = ["jpg", "png"]
        doc_target = ["txt", "json", "yml", "yaml"]
        model_target = ["onnx", "pt", "pth"]

        BASE_REGEX = rf"(?={prefix})" + r"[A-Za-z0-9_-]+\."

        REGEX = BASE_REGEX + "(" + "|".join(image_target + doc_target + model_target) + ")"
        self.classifier = re.compile(REGEX)

    def __call__(self, path):
        ext = self._check_extension(path)
        return DECHIPERS[ext](path, self.key)

    def _check_extension(self, path):
        name = os.path.basename(path)
        print("\033[95m" + f"{path}" + "\033[m")
        print("\033[95m" + f"{self.prefix}" + "\033[m")
        assert self.classifier.search(name) != None
        name = name.split(".")
        return name[-1]


DECHIPERS = {
    "jpg": None,
    "png": solver.png_solver,
    "txt": solver.txt_solver,
    "json": solver.json_solver,
    "yaml": solver.yaml_solver,
    "yml": solver.yaml_solver,
    "onnx": solver.onnx_solver,
    "pth": solver.pth_solver,
    "pt": solver.pth_solver,
    "ts": solver.pth_solver,
}
