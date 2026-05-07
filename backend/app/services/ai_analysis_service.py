from collections import Counter, defaultdict
from statistics import mean


def analyze_detection_results(results: list[dict]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "summary": "Detected 0 objects across 0 classes.",
            "class_distribution": [],
            "anomaly_tips": ["No objects were detected in the submitted source."],
        }

    counts = Counter(item["class"] for item in results)
    confidences: dict[str, list[float]] = defaultdict(list)
    bbox_areas: list[float] = []
    for item in results:
        confidences[item["class"]].append(float(item["confidence"]))
        x1, y1, x2, y2 = item["bbox"]
        bbox_areas.append(max(0.0, float(x2) - float(x1)) * max(0.0, float(y2) - float(y1)))

    distribution = [
        {
            "class": class_name,
            "count": count,
            "avg_confidence": round(mean(confidences[class_name]), 4),
            "ratio": round(count / total, 4),
        }
        for class_name, count in counts.most_common()
    ]

    tips: list[str] = []
    average_confidence = mean(float(item["confidence"]) for item in results)
    dominant_class, dominant_count = counts.most_common(1)[0]
    if dominant_count / total >= 0.8 and total >= 5:
        tips.append(f"Class distribution is concentrated: {dominant_class} accounts for {dominant_count}/{total} objects.")
    if average_confidence < 0.5:
        tips.append("Average confidence is below 0.50; consider checking model fit, input quality, or threshold settings.")
    if bbox_areas:
        avg_area = mean(bbox_areas)
        tiny_count = sum(1 for area in bbox_areas if avg_area > 0 and area < avg_area * 0.05)
        huge_count = sum(1 for area in bbox_areas if avg_area > 0 and area > avg_area * 5)
        if tiny_count:
            tips.append(f"Detected {tiny_count} unusually small bounding boxes; review possible false positives.")
        if huge_count:
            tips.append(f"Detected {huge_count} unusually large bounding boxes; review source scale or close-range objects.")
    if not tips:
        tips.append("No obvious statistical anomalies were found in the detection results.")

    return {
        "summary": f"Detected {total} objects across {len(counts)} classes.",
        "class_distribution": distribution,
        "anomaly_tips": tips,
    }
