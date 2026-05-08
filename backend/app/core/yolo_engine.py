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
        self._requested_device = settings.yolo_device or "auto"
        self._device = self._resolve_device(self._requested_device, allow_auto_fallback=True)
        self._class_names: list[str] = []
        self._warmup_status = "idle"
        self._warmup_error = ""
        self._initialized = True

    def _detect_device(self) -> str:
        try:
            import torch

            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _cuda_device_count(self) -> int:
        try:
            import torch

            return int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
        except Exception:
            return 0

    def _resolve_device(self, requested_device: str | None, allow_auto_fallback: bool = False) -> str:
        requested = (requested_device or "auto").strip().lower()
        if requested == "auto":
            return self._detect_device()
        if requested == "cpu":
            return "cpu"
        if requested == "cuda":
            requested = "cuda:0"
        if requested.startswith("cuda:"):
            try:
                index = int(requested.split(":", 1)[1])
            except ValueError as exc:
                raise AppException(40024, f"Invalid CUDA device: {requested_device}") from exc
            count = self._cuda_device_count()
            if 0 <= index < count:
                return f"cuda:{index}"
            if allow_auto_fallback:
                return "cpu"
            raise AppException(40025, f"CUDA device {requested} is not available")
        raise AppException(40024, f"Unsupported YOLO device: {requested_device}")

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
    def requested_device(self) -> str:
        return self._requested_device

    @property
    def class_names(self) -> list[str]:
        return list(self._class_names)

    def cuda_available(self) -> bool:
        return self._cuda_device_count() > 0

    def cuda_name(self, index: int = 0) -> str:
        try:
            import torch

            if torch.cuda.is_available() and index < torch.cuda.device_count():
                return str(torch.cuda.get_device_name(index))
        except Exception:
            return ""
        return ""

    def available_devices(self) -> list[dict[str, Any]]:
        devices: list[dict[str, Any]] = [{"value": "auto", "label": "自动选择", "type": "auto", "available": True}]
        devices.append({"value": "cpu", "label": "CPU", "type": "cpu", "available": True})
        try:
            import torch

            if torch.cuda.is_available():
                for index in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(index)
                    devices.append(
                        {
                            "value": f"cuda:{index}",
                            "label": props.name,
                            "type": "cuda",
                            "available": True,
                            "total_memory": int(props.total_memory),
                        }
                    )
        except Exception:
            pass
        return devices

    def device_resolution_reason(self) -> str:
        requested = (self._requested_device or "auto").lower()
        if requested == "cpu":
            return "用户配置强制使用 CPU"
        if requested == "auto" and self._device.startswith("cuda"):
            return "自动选择可用 CUDA 设备"
        if requested == "auto" and self._device == "cpu":
            return "自动模式未检测到 CUDA，回退到 CPU"
        if requested.startswith("cuda"):
            return "用户指定 CUDA 设备"
        return "使用当前 YOLO 设备配置"

    def state(self) -> dict[str, Any]:
        return {
            "engine_loaded": self.is_loaded,
            "device": self._device,
            "requested_device": self._requested_device,
            "device_resolution_reason": self.device_resolution_reason(),
            "available_devices": self.available_devices(),
            "cuda_available": self.cuda_available(),
            "cuda_name": self.cuda_name(),
            "model_path": self._model_path,
            "class_names": self.class_names,
            "warmup_status": self._warmup_status,
            "warmup_error": self._warmup_error,
        }

    def load_model(self, model_path: str, device: str | None = None) -> None:
        path = Path(model_path)
        if not path.exists():
            raise AppException(40001, f"Model file not found: {model_path}")
        with self._lock:
            from ultralytics import YOLO

            if device is not None:
                self._requested_device = device
            next_device = self._resolve_device(self._requested_device)
            next_model = YOLO(str(path))
            names = getattr(next_model, "names", {}) or {}
            class_names = self._normalize_names(names)
            self._model = next_model
            self._model_path = str(path)
            self._device = next_device
            self._class_names = class_names
            self._warmup_status = "pending"
            self._warmup_error = ""

    def switch_model(self, model_path: str, device: str | None = None) -> None:
        self.load_model(model_path, device=device)

    def set_device(self, device: str) -> dict[str, Any]:
        with self._lock:
            self._requested_device = device
            self._device = self._resolve_device(device)
            self._warmup_status = "pending" if self._model is not None else "not_loaded"
            self._warmup_error = ""
            if self._model is not None:
                return self.warmup()
            return self.state()

    def warmup(self) -> dict[str, Any]:
        with self._lock:
            if self._model is None:
                self._warmup_status = "not_loaded"
                self._warmup_error = ""
                return self.state()
            try:
                self._device = self._resolve_device(self._requested_device)
                self._run_warmup(self._device)
                self._warmup_status = "cuda_ready" if self._device.startswith("cuda") else "cpu_ready"
                self._warmup_error = ""
            except Exception as exc:
                if self._requested_device == "auto":
                    cuda_error = str(exc)
                    self._device = "cpu"
                    try:
                        self._run_warmup("cpu")
                        self._warmup_status = "cpu_ready"
                        self._warmup_error = f"CUDA warmup failed, using CPU: {cuda_error}"
                    except Exception as cpu_exc:
                        self._warmup_status = "failed"
                        self._warmup_error = str(cpu_exc)
                else:
                    self._warmup_status = "failed"
                    self._warmup_error = str(exc)
                    raise
            return self.state()

    def _run_warmup(self, device: str) -> None:
        import numpy as np

        dummy = np.zeros((64, 64, 3), dtype=np.uint8)
        self._model.predict(
            source=[dummy],
            conf=settings.confidence_threshold,
            device=device,
            verbose=False,
            imgsz=64,
        )

    def predict_image(self, source: Any, conf: float | None = None, iou: float | None = None) -> list[dict[str, Any]]:
        return self.predict_batch([source], conf=conf, iou=iou)[0]

    def predict_batch(self, sources: list[Any], conf: float | None = None, iou: float | None = None) -> list[list[dict[str, Any]]]:
        if not sources:
            return []
        with self._lock:
            if self._model is None:
                raise AppException(40002, "No YOLO model is loaded")
            results = self._model.predict(
                source=sources,
                conf=settings.confidence_threshold if conf is None else conf,
                iou=settings.iou_threshold if iou is None else iou,
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
