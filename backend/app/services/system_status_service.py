from app.core.yolo_engine import yolo_engine


def get_system_status() -> dict:
    cpu_percent = None
    memory = None
    temperature = None
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory = {
            "total": int(memory_info.total),
            "available": int(memory_info.available),
            "used": int(memory_info.used),
            "percent": float(memory_info.percent),
        }
        try:
            temps = psutil.sensors_temperatures()
            readings = [entry.current for entries in temps.values() for entry in entries if entry.current is not None]
            temperature = round(sum(readings) / len(readings), 2) if readings else None
        except Exception:
            temperature = None
    except Exception:
        pass

    gpu_devices = []
    torch_version = ""
    torch_cuda_version = ""
    cuda_available = False
    cuda_device_count = 0
    cuda_error = ""
    try:
        import torch

        torch_version = str(torch.__version__)
        torch_cuda_version = str(torch.version.cuda or "")
        cuda_available = bool(torch.cuda.is_available())
        cuda_device_count = int(torch.cuda.device_count()) if cuda_available else 0
        if cuda_available:
            for index in range(cuda_device_count):
                props = torch.cuda.get_device_properties(index)
                gpu_devices.append(
                    {
                        "index": index,
                        "name": props.name,
                        "total_memory": int(props.total_memory),
                        "allocated_memory": int(torch.cuda.memory_allocated(index)),
                        "reserved_memory": int(torch.cuda.memory_reserved(index)),
                        "temperature": gpu_temperature(index),
                    }
                )
    except Exception as exc:
        cuda_error = str(exc)

    engine_state = yolo_engine.state()
    diagnostics = build_gpu_diagnostics(engine_state, torch_version, torch_cuda_version, cuda_available, cuda_device_count, cuda_error)
    return {
        "cpu_percent": cpu_percent,
        "memory": memory,
        "temperature": temperature,
        "gpu_devices": gpu_devices,
        "torch_version": torch_version,
        "torch_cuda_version": torch_cuda_version,
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_device_count,
        "cuda_error": cuda_error,
        "diagnostics": diagnostics,
        "engine": engine_state,
    }


def build_gpu_diagnostics(
    engine_state: dict,
    torch_version: str,
    torch_cuda_version: str,
    cuda_available: bool,
    cuda_device_count: int,
    cuda_error: str,
) -> dict:
    requested_device = engine_state.get("requested_device") or "auto"
    resolved_device = engine_state.get("device") or ""
    warmup_error = engine_state.get("warmup_error") or ""
    checks = []
    if not torch_version:
        checks.append({"name": "PyTorch", "status": "error", "message": "未检测到 PyTorch，无法使用 CUDA 推理。"})
    else:
        checks.append({"name": "PyTorch", "status": "ok", "message": f"PyTorch 版本：{torch_version}"})
    if not torch_cuda_version:
        checks.append({"name": "CUDA 运行时", "status": "warning", "message": "当前 PyTorch 未包含 CUDA 运行时，通常只能使用 CPU。"})
    else:
        checks.append({"name": "CUDA 运行时", "status": "ok", "message": f"PyTorch CUDA 版本：{torch_cuda_version}"})
    if cuda_available and cuda_device_count > 0:
        checks.append({"name": "CUDA 设备", "status": "ok", "message": f"检测到 {cuda_device_count} 个 CUDA 设备。"})
    else:
        message = cuda_error or "torch.cuda.is_available() 返回 False，请检查显卡驱动、CUDA 版本和 PyTorch 安装。"
        checks.append({"name": "CUDA 设备", "status": "error", "message": message})
    if requested_device == "cpu":
        checks.append({"name": "YOLO 设备配置", "status": "warning", "message": "当前配置强制使用 CPU。"})
    elif str(requested_device).startswith("cuda") and not resolved_device.startswith("cuda"):
        checks.append({"name": "YOLO 设备配置", "status": "error", "message": f"请求 {requested_device}，实际运行在 {resolved_device or '未知设备'}。"})
    else:
        checks.append({"name": "YOLO 设备配置", "status": "ok", "message": f"请求设备：{requested_device}，实际设备：{resolved_device or '未加载'}。"})
    if warmup_error:
        checks.append({"name": "模型预热", "status": "warning", "message": warmup_error})
    elif engine_state.get("warmup_status") in {"cuda_ready", "cpu_ready"}:
        checks.append({"name": "模型预热", "status": "ok", "message": f"预热状态：{engine_state.get('warmup_status')}。"})
    else:
        checks.append({"name": "模型预热", "status": "info", "message": f"预热状态：{engine_state.get('warmup_status') or 'idle'}。"})
    return {
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "torch_version": torch_version,
        "torch_cuda_version": torch_cuda_version,
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_device_count,
        "warmup_error": warmup_error,
        "checks": checks,
    }


def gpu_temperature(index: int) -> float | None:
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
        return float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
    except Exception:
        return None
