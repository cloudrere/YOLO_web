import threading
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.response import AppException


class YoloEngine:
    _instance: "YoloEngine | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._model: Any | None = None
        self._model_path = ""
        self._device = self._detect_device()
        self._class_names: list[str] = []
        self._initialized = True

    def _detect_device(self) -> str:
        try:
            import torch

            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_path(self) -> str:
        return self._model_path

    @property
    def device(self) -> str:
        return self._device

    @property
    def class_names(self) -> list[str]:
        return list(self._class_names)

    def cuda_available(self) -> bool:
        try:
            import torch

            return bool(torch.cuda.is_available())
        except Exception:
            return False

    def state(self) -> dict[str, Any]:
        return {
            "engine_loaded": self.is_loaded,
            "device": self._device,
            "cuda_available": self.cuda_available(),
            "model_path": self._model_path,
            "class_names": self.class_names,
        }

    def load_model(self, model_path: str) -> None:
        path = Path(model_path)
        if not path.exists():
            raise AppException(40001, f"Model file not found: {model_path}")
        with self._lock:
            from ultralytics import YOLO

            next_device = self._detect_device()
            next_model = YOLO(str(path))
            names = getattr(next_model, "names", {}) or {}
            class_names = self._normalize_names(names)
            self._model = next_model
            self._model_path = str(path)
            self._device = next_device
            self._class_names = class_names

    def switch_model(self, model_path: str) -> None:
        path = Path(model_path)
        if not path.exists():
            raise AppException(40001, f"Model file not found: {model_path}")
        with self._lock:
            from ultralytics import YOLO

            next_device = self._detect_device()
            next_model = YOLO(str(path))
            names = getattr(next_model, "names", {}) or {}
            class_names = self._normalize_names(names)
            self._model = next_model
            self._model_path = str(path)
            self._device = next_device
            self._class_names = class_names

    def predict_image(self, source: Any, conf: float | None = None) -> list[dict[str, Any]]:
        return self.predict_batch([source], conf=conf)[0]

    def predict_batch(self, sources: list[Any], conf: float | None = None) -> list[list[dict[str, Any]]]:
        if not sources:
            return []
        with self._lock:
            if self._model is None:
                raise AppException(40002, "No YOLO model is loaded")
            results = self._model.predict(
                source=sources,
                conf=settings.confidence_threshold if conf is None else conf,
                device=self._device,
                verbose=False,
            )
            return [self._parse_result(result) for result in results]

    def _normalize_names(self, names: Any) -> list[str]:
        if isinstance(names, dict):
            return [str(names[index]) for index in sorted(names)]
        if isinstance(names, list):
            return [str(item) for item in names]
        return []

    def _parse_result(self, result: Any) -> list[dict[str, Any]]:
        names = getattr(result, "names", None) or getattr(self._model, "names", {}) or {}
        parsed: list[dict[str, Any]] = []
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return parsed
        for box in boxes:
            xyxy = box.xyxy[0].detach().cpu().tolist()
            confidence = float(box.conf[0].detach().cpu().item())
            class_index = int(box.cls[0].detach().cpu().item())
            class_name = str(names.get(class_index, class_index) if isinstance(names, dict) else names[class_index])
            parsed.append(
                {
                    "class": class_name,
                    "confidence": confidence,
                    "bbox": [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])],
                }
            )
        return parsed


yolo_engine = YoloEngine()
