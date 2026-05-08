from pathlib import Path

import cv2
import numpy as np

_CLASS_COLORS = [
    (46, 139, 87),
    (54, 108, 214),
    (216, 159, 50),
    (184, 74, 58),
    (122, 92, 201),
    (46, 161, 176),
    (82, 167, 71),
    (213, 101, 46),
    (190, 65, 127),
    (86, 132, 54),
]


def _class_color(class_name: str) -> tuple[int, int, int]:
    index = sum(class_name.encode("utf-8")) % len(_CLASS_COLORS)
    return _CLASS_COLORS[index]


def draw_detections(frame: np.ndarray, detections: list[dict]) -> np.ndarray:
    output = frame.copy()
    for item in detections:
        x1, y1, x2, y2 = [int(v) for v in item["bbox"]]
        label = f"{item['class']} {item['confidence']:.2f}"
        color = _class_color(str(item.get("class", "")))
        text_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_y = max(text_size[1] + 8, y1 - 8)
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        cv2.rectangle(output, (x1, text_y - text_size[1] - 8), (x1 + text_size[0] + 8, text_y + baseline), color, -1)
        cv2.putText(output, label, (x1 + 4, text_y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return output


def write_frame(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame)
