from pathlib import Path

import cv2
import numpy as np


def draw_detections(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    output = frame.copy()
    for item in detections:
        x1, y1, x2, y2 = [int(v) for v in item["bbox"]]
        label = f"{item['class']} {item['confidence']:.2f}"
        cv2.rectangle(output, (x1, y1), (x2, y2), (46, 139, 87), 2)
        cv2.putText(output, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (46, 139, 87), 2)
    return output


def write_frame(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame)
