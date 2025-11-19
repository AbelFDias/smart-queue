from typing import List, Tuple


Point = Tuple[int, int]


def compute_queue_length(centroids: List[Point], x_line: int, direction: str) -> int:
    if not centroids:
        return 0
    if direction == 'left_to_right':
        return sum(1 for (x, _) in centroids if x < x_line)
    return sum(1 for (x, _) in centroids if x > x_line)


def estimate_eta(queue_len: int, avg_service_time_sec: int) -> int:
    if queue_len <= 0 or avg_service_time_sec <= 0:
        return 0
    return int(queue_len * avg_service_time_sec)
