import cv2
from typing import List, Dict, Any


def detect_people(model, frame, conf: float) -> List[Dict[str, Any]]:
    """
    Detecta pessoas num frame usando YOLOv8 local.

    Returns lista de detecções: dicts com x1,y1,x2,y2,confidence
    """
    results = model(frame, conf=conf, classes=[0], verbose=False)

    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf_val = float(box.conf[0])
            detections.append({
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2),
                'confidence': conf_val
            })
    return detections


def draw_detections(frame, detections):
    for det in detections:
        x1, y1 = det['x1'], det['y1']
        x2, y2 = det['x2'], det['y2']
        conf = det['confidence']

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        label = f"Pessoa: {conf:.0%}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        label_w, label_h = label_size
        cv2.rectangle(frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), (0, 255, 0), -1)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    return frame


def draw_info(
    frame,
    fps: float,
    num_people: int,
    entries: int,
    direction: str,
    band_px: int,
    queue_len: int,
    eta_sec: int,
    debug: bool = False,
    show_eta: bool = False,
):
    overlay = frame.copy()
    # Expand HUD area to fit more lines
    cv2.rectangle(overlay, (10, 10), (360, 140), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    y = 35
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    y += 25
    cv2.putText(frame, f"Pessoas: {num_people}", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    y += 25
    dir_label = 'L->R' if direction == 'left_to_right' else 'R->L'
    cv2.putText(frame, f"Entradas: {entries}  Dir: {dir_label}", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    y += 25
    if show_eta:
        mm, ss = divmod(int(eta_sec), 60)
        cv2.putText(frame, f"Fila: {queue_len}  ETA: {mm:02d}:{ss:02d}  Banda: {band_px}px", (20, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    if debug:
        # small marker to indicate debug on
        cv2.circle(frame, (340, 24), 6, (0, 0, 255), -1)
    return frame
