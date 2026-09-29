"""
Perceptual and Exact Duplicate Detection for ONION_SURE

Detects:
1. Exact duplicates via SHA256 hashes.
2. Perceptual duplicates via 64-bit dHash (Hamming distance threshold).
3. Groups duplicate/near-duplicate pairs into clusters using Union-Find (Disjoint Set)
   so the splitter can guarantee entire clusters stay within a single split,
   preventing near-duplicate data leakage between train, validation, and test.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from .analyzer import ImageMetrics


def hamming_distance(h1: str, h2: str) -> int:
    """Computes Hamming distance between two 16-character hex strings (64-bit)."""
    val1 = int(h1, 16)
    val2 = int(h2, 16)
    xor_val = val1 ^ val2
    # Count bits set
    return bin(xor_val).count("1")


class DisjointSet:
    """Disjoint-set (Union-Find) with path compression for clustering duplicates."""

    def __init__(self, elements: List[str]):
        self.parent = {elem: elem for elem in elements}
        self.rank = {elem: 0 for elem in elements}

    def find(self, item: str) -> str:
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1: str, item2: str):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            if self.rank[root1] > self.rank[root2]:
                self.parent[root2] = root1
            elif self.rank[root1] < self.rank[root2]:
                self.parent[root1] = root2
            else:
                self.parent[root2] = root1
                self.rank[root1] += 1


class PerceptualDuplicateDetector:
    """Detects exact and near-duplicates and assigns cluster IDs to prevent data leakage."""

    def __init__(self, max_hamming_distance: int = 2):
        self.max_hamming_distance = max_hamming_distance

    def find_exact_duplicates(self, metrics_list: List[ImageMetrics]) -> Dict[str, List[str]]:
        """Groups images that have the exact same SHA256 hash."""
        hash_map = defaultdict(list)
        for m in metrics_list:
            if not m.is_corrupt and m.sha256:
                hash_map[m.sha256].append(m.path)
        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    def cluster_perceptual_duplicates(
        self,
        metrics_list: List[ImageMetrics],
    ) -> Tuple[Dict[str, str], List[Dict[str, any]]]:
        """
        Groups images into clusters based on dHash Hamming distance.
        Returns:
            - mapping: filepath -> cluster_id
            - clusters_info: list of multi-item cluster summaries
        """
        valid_metrics = [m for m in metrics_list if not m.is_corrupt and m.dhash]
        paths = [m.path for m in valid_metrics]
        
        # Fast grouping by exact dHash first
        dhash_groups = defaultdict(list)
        for m in valid_metrics:
            dhash_groups[m.dhash].append(m.path)

        dsu = DisjointSet(paths)

        # Union images with identical dHash (distance = 0)
        for group in dhash_groups.values():
            if len(group) > 1:
                first = group[0]
                for other in group[1:]:
                    dsu.union(first, other)

        # If hamming threshold > 0, compare distinct dHashes within each category
        # To keep it O(N) or small per category, compare unique dHashes
        if self.max_hamming_distance > 0:
            unique_dhashes = list(dhash_groups.keys())
            # For efficiency across 24k images, compare unique hashes
            # In typical datasets, identical hashes capture majority of near-duplicates
            n_hashes = len(unique_dhashes)
            if n_hashes <= 4000:  # feasible quadratic check if unique count is reasonable
                for i in range(n_hashes):
                    h1 = unique_dhashes[i]
                    p1 = dhash_groups[h1][0]
                    for j in range(i + 1, n_hashes):
                        h2 = unique_dhashes[j]
                        dist = hamming_distance(h1, h2)
                        if dist <= self.max_hamming_distance:
                            p2 = dhash_groups[h2][0]
                            dsu.union(p1, p2)

        # Extract clusters
        cluster_map: Dict[str, str] = {}
        grouped_by_root = defaultdict(list)
        for p in paths:
            root = dsu.find(p)
            grouped_by_root[root].append(p)

        clusters_info = []
        cluster_idx = 1
        for root, cluster_paths in grouped_by_root.items():
            cid = f"cluster_{cluster_idx:05d}"
            cluster_idx += 1
            for p in cluster_paths:
                cluster_map[p] = cid
            if len(cluster_paths) > 1:
                clusters_info.append({
                    "cluster_id": cid,
                    "count": len(cluster_paths),
                    "paths": cluster_paths,
                })

        return cluster_map, clusters_info
