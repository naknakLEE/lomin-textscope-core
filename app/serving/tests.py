import torch
import onnx
import onnxruntime


def to_numpy(tensor):
    if tensor.requires_grad:
        return tensor.detach().cpu().numpy()
    else:
        return tensor.cpu().numpy()


providers = [
    (
        "CUDAExecutionProvider",
        {
            "device_id": 0,
        },
    ),
    # 'CPUExecutionProvider',
]
example = torch.rand(1, 3, 30, 128).to("cuda")
# inputs = torch.from_numpy(cropped_images).to("cuda")
inputs = example
output_path = "/workspace/assets/models/baseline_exp1_-epoch=2_acc=0.onnx"
exported_model = onnx.load(output_path)
onnx.checker.check_model(exported_model)
ort_session = onnxruntime.InferenceSession(output_path, providers=providers)
# compute ONNX Runtime output prediction
ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(inputs)}
ort_outs = ort_session.run(None, ort_inputs)
# np.testing.assert_allclose(to_numpy(torch_out), ort_outs[0], rtol=1e-03, atol=1e-05)
rec_preds = [ort_outs]
print("\033[95m" + f"{rec_preds}" + "\033[m")
