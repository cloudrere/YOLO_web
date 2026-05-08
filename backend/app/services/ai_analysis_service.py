from collections import Counter, defaultdict
from statistics import mean


def analyze_detection_results(results: list[dict]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "summary": "本次未检测到目标。",
            "class_distribution": [],
            "anomaly_tips": ["当前来源未检出目标，可检查输入质量、模型类别或降低置信度阈值。"],
        }

    counts = Counter(item["class"] for item in results)
    class_zh_map = {item["class"]: item.get("class_zh", item["class"]) for item in results}
    confidences: dict[str, list[float]] = defaultdict(list)
    bbox_areas: list[float] = []
    for item in results:
        confidences[item["class"]].append(float(item["confidence"]))
        x1, y1, x2, y2 = item["bbox"]
        bbox_areas.append(max(0.0, float(x2) - float(x1)) * max(0.0, float(y2) - float(y1)))

    distribution = [
        {
            "class": class_name,
            "class_zh": class_zh_map.get(class_name, class_name),
            "count": count,
            "avg_confidence": round(mean(confidences[class_name]), 4),
            "ratio": round(count / total, 4),
        }
        for class_name, count in counts.most_common()
    ]

    tips: list[str] = []
    average_confidence = mean(float(item["confidence"]) for item in results)
    dominant_class, dominant_count = counts.most_common(1)[0]
    dominant_text = class_zh_map.get(dominant_class, dominant_class)
    if dominant_count / total >= 0.8 and total >= 5:
        tips.append(f"类别分布较集中：{dominant_text} 占 {dominant_count}/{total} 个目标。")
    if average_confidence < 0.5:
        tips.append("平均置信度低于 0.50，建议检查模型适配度、输入质量或阈值设置。")
    if bbox_areas:
        avg_area = mean(bbox_areas)
        tiny_count = sum(1 for area in bbox_areas if avg_area > 0 and area < avg_area * 0.05)
        huge_count = sum(1 for area in bbox_areas if avg_area > 0 and area > avg_area * 5)
        if tiny_count:
            tips.append(f"检测到 {tiny_count} 个异常小框，建议复核是否存在误检。")
        if huge_count:
            tips.append(f"检测到 {huge_count} 个异常大框，建议检查画面尺度或近距离目标。")
    if not tips:
        tips.append("未发现明显统计异常，检测结果分布相对稳定。")

    return {
        "summary": f"本次共检测到 {total} 个目标，覆盖 {len(counts)} 个类别。",
        "class_distribution": distribution,
        "anomaly_tips": tips,
    }
