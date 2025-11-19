from typing import List, Tuple, Dict


class SimpleTracker:
    """
    Minimal centroid tracker with greedy one-to-one matching.
    Keeps only last centroid and a small miss TTL per track.
    """
    def __init__(self, match_radius_px: int = 60, ttl: int = 6) -> None:
        self.match_radius_px = match_radius_px
        self.ttl = ttl
        self._next_id = 1
        # tracks: id -> { 'centroid': (x,y), 'miss': int }
        self.tracks: Dict[int, Dict] = {}

    def update(self, centroids: List[Tuple[int, int]]) -> List[Tuple[int, Tuple[int, int], Tuple[int, int]]]:
        """
        Update tracker with current centroids.
        Returns list of matched (track_id, prev_centroid, curr_centroid).
        """
        matched: List[Tuple[int, Tuple[int, int], Tuple[int, int]]] = []

        if not self.tracks and not centroids:
            return matched

        # Build candidate pairs (track_id, idx, d2) within radius
        pairs = []
        max_d2 = self.match_radius_px * self.match_radius_px
        for tid, t in self.tracks.items():
            px, py = t['centroid']
            for i, (cx, cy) in enumerate(centroids):
                dx, dy = cx - px, cy - py
                d2 = dx * dx + dy * dy
                if d2 <= max_d2:
                    pairs.append((d2, tid, i))

        # Greedy one-to-one assign by nearest distance first
        pairs.sort(key=lambda x: x[0])
        used_tracks = set()
        used_indices = set()
        for _, tid, idx in pairs:
            if tid in used_tracks or idx in used_indices:
                continue
            prev_c = self.tracks[tid]['centroid']
            curr_c = centroids[idx]
            matched.append((tid, prev_c, curr_c))
            self.tracks[tid]['centroid'] = curr_c
            self.tracks[tid]['miss'] = 0
            used_tracks.add(tid)
            used_indices.add(idx)

        # Create new tracks for unmatched centroids
        for i, c in enumerate(centroids):
            if i in used_indices:
                continue
            tid = self._next_id
            self._next_id += 1
            self.tracks[tid] = {'centroid': c, 'miss': 0}

        # Age and remove missed tracks
        to_delete = []
        for tid, t in self.tracks.items():
            if tid in used_tracks:
                continue
            t['miss'] += 1
            if t['miss'] > self.ttl:
                to_delete.append(tid)
        for tid in to_delete:
            del self.tracks[tid]

        return matched
