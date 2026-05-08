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
    try:
        import torch

        if torch.cuda.is_available():
            for index in range(torch.cuda.device_count()):
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
    except Exception:
        pass

    return {
        "cpu_percent": cpu_percent,
        "memory": memory,
        "temperature": temperature,
        "gpu_devices": gpu_devices,
        "engine": yolo_engine.state(),
    }


def gpu_temperature(index: int) -> float | None:
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
        return float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
    except Exception:
        return None
