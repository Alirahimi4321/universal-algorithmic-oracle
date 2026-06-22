"""ONNX Runtime inference engine."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_ONNX = False
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    pass


class ONNXInferenceEngine:
    """Run ONNX models for inference."""

    def __init__(self):
        self.available = HAS_ONNX

    def run_inference(self, model_path: str, input_data: dict) -> dict:
        if not self.available:
            return {"error": "onnxruntime not available"}
        try:
            session = ort.InferenceSession(model_path)
            input_name = session.get_inputs()[0].name
            input_array = np.array(input_data.get("input", [[1.0, 2.0, 3.0]]))
            outputs = session.run(None, {input_name: input_array})
            return {
                "outputs": [o.tolist() for o in outputs],
                "output_names": [o.name for o in session.get_outputs()],
                "input_shape": list(input_array.shape),
            }
        except Exception as e:
            logger.warning("onnxruntime failed: %s", e)
            return {"error": str(e)}

    def get_model_info(self, model_path: str) -> dict:
        if not self.available:
            return {"error": "onnxruntime not available"}
        try:
            session = ort.InferenceSession(model_path)
            inputs = [{"name": i.name, "shape": i.shape, "type": i.type} for i in session.get_inputs()]
            outputs = [{"name": o.name, "shape": o.shape, "type": o.type} for o in session.get_outputs()]
            return {"inputs": inputs, "outputs": outputs, "providers": session.get_providers()}
        except Exception as e:
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        model_path = data.get("model_path")
        if not model_path:
            return {"error": "model_path required", "providers": ort.get_available_providers() if HAS_ONNX else []}
        return self.run_inference(model_path, data)
