import unittest
import onnxruntime as ort
import argparse
import torch
import numpy as np
import io
from crypto import Crypto

class ONNXCryptoTester(unittest.TestCase):
    def test_onnx_crypto(self):
        c = Crypto()

        with open(args.key, "rb") as f:
            key = f.read()
        with open(args.origin, "rb") as f:
            io_origin = f.read()
            io_origin = io.BytesIO(io_origin)
        with open(args.crypted, "rb") as f:
            io_crypted = f.read()
            io_crypted = c.decrypt(io_crypted, key)
            io_crypted = io.BytesIO(io_crypted)

        self.ort_validate(io_origin, io_crypted)

    def ort_validate(self, onnx_io_1, onnx_io_2):
        inputs = (torch.rand(3, 800, 1088),)
        def to_numpy(tensor):
            if tensor.requires_grad:
                return tensor.detach().cpu().numpy()
            else:
                return tensor.cpu().numpy()

        inputs = list(map(to_numpy, inputs))

        ort_session_1 = ort.InferenceSession(onnx_io_1.getvalue())
        ort_session_2 = ort.InferenceSession(onnx_io_2.getvalue())
        
        # compute onnxruntime output prediction
        ort_inputs = dict((ort_session_1.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs))
        ort_outs_1 = ort_session_1.run(None, ort_inputs)
        ort_outs_2 = ort_session_2.run(None, ort_inputs)
        self.validate(ort_outs_1, ort_outs_2)

    def validate(self, ort_outs_1, ort_outs_2):
        for i in range(0, len(ort_outs_1)):
            torch.testing.assert_allclose(ort_outs_1[i].astype(np.float32), ort_outs_2[i].astype(np.float32), rtol=1e-02, atol=1e-04)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--origin", type=str, required=True)
    parser.add_argument("-c", "--crypted", type=str, required=True)
    parser.add_argument("-k", "--key", type=str, required=True)
    args = parser.parse_args()

    unittest.main(__name__, argv=['main'])
