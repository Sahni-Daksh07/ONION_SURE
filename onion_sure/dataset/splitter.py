"""
Cluster-Aware Dataset Splitting for ONION_SURE

Guarantees:
1. Strict Stratification across part, condition, and subcategory.
2. Cluster-Aware Split: Entire perceptual/duplicate clusters are assigned atomically
   to the same split, completely preventing near-duplicate leakage between train, val, and test.
3. Fixed random seed (42) for deterministic reproducibility.
"""

import random
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from .analyzer import ImageMetrics


class ClusterAwareSplitter:
    """Splits dataset into train/val/test while preventing duplicate/cluster leakage."""

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed

    def split(
        self,
        metrics_list: List[ImageMetrics],
        cluster_map: Dict[str, str],
    ) -> Dict[str, any]:
        # Filter valid non-corrupt images
        valid_items = [m for m in metrics_list if not m.is_corrupt]
        total_valid = len(valid_items)

        # Group items by stratum and cluster
        # Key: stratum_key -> Dict[cluster_id, List[ImageMetrics]]
        strata: Dict[str, Dict[str, List[ImageMetrics]]] = defaultdict(lambda: defaultdict(list))
        for m in valid_items:
            stratum_key = f"{m.part}/{m.condition}/{m.subcategory}"
            cid = cluster_map.get(m.path, m.path)
            strata[stratum_key][cid].append(m)

        rng = random.Random(self.random_seed)

        train_paths: List[str] = []
        val_paths: List[str] = []
        test_paths: List[str] = []

        strata_summary = {}

        for stratum_key in sorted(strata.keys()):
            clusters_dict = strata[stratum_key]
            # List of clusters (each cluster is a list of ImageMetrics)
            cluster_keys = sorted(clusters_dict.keys())
            rng.shuffle(cluster_keys)

            stratum_total_images = sum(len(clusters_dict[ck]) for ck in cluster_keys)
            target_train = int(round(stratum_total_images * self.train_ratio))
            target_val = int(round(stratum_total_images * self.val_ratio))

            s_train, s_val, s_test = [], [], []
            curr_train_count, curr_val_count = 0, 0

            for ck in cluster_keys:
                items = clusters_dict[ck]
                item_paths = [m.path for m in items]
                cnt = len(item_paths)

                # Greedy cluster assignment respecting targets
                if curr_train_count + cnt <= target_train or (curr_train_count < target_train and not s_train):
                    s_train.extend(item_paths)
                    curr_train_count += cnt
                elif curr_val_count + cnt <= target_val or (curr_val_count < target_val and not s_val):
                    s_val.extend(item_paths)
                    curr_val_count += cnt
                else:
                    s_test.extend(item_paths)

            train_paths.extend(s_train)
            val_paths.extend(s_val)
            test_paths.extend(s_test)

            strata_summary[stratum_key] = {
                "total": stratum_total_images,
                "train": len(s_train),
                "val": len(s_val),
                "test": len(s_test),
                "train_pct": round(len(s_train) / stratum_total_images * 100, 2) if stratum_total_images else 0,
            }

        # Assert no data leakage between any split
        train_set = set(train_paths)
        val_set = set(val_paths)
        test_set = set(test_paths)

        leak_train_val = train_set.intersection(val_set)
        leak_train_test = train_set.intersection(test_set)
        leak_val_test = val_set.intersection(test_set)

        assert not leak_train_val, f"Leakage between train and val: {len(leak_train_val)}"
        assert not leak_train_test, f"Leakage between train and test: {len(leak_train_test)}"
        assert not leak_val_test, f"Leakage between val and test: {len(leak_val_test)}"

        # Assert cluster isolation (no cluster has images in more than one split)
        cluster_to_split: Dict[str, str] = {}
        for p in train_paths:
            cid = cluster_map.get(p, p)
            if cid in cluster_to_split:
                assert cluster_to_split[cid] == "train", f"Cluster {cid} leaked into train!"
            cluster_to_split[cid] = "train"

        for p in val_paths:
            cid = cluster_map.get(p, p)
            if cid in cluster_to_split:
                assert cluster_to_split[cid] == "val", f"Cluster {cid} leaked into val!"
            cluster_to_split[cid] = "val"

        for p in test_paths:
            cid = cluster_map.get(p, p)
            if cid in cluster_to_split:
                assert cluster_to_split[cid] == "test", f"Cluster {cid} leaked into test!"
            cluster_to_split[cid] = "test"

        return {
            "random_seed": self.random_seed,
            "total_images": total_valid,
            "split_summary": {
                "train": {"count": len(train_paths), "percentage": round(len(train_paths) / total_valid * 100, 2)},
                "val": {"count": len(val_paths), "percentage": round(len(val_paths) / total_valid * 100, 2)},
                "test": {"count": len(test_paths), "percentage": round(len(test_paths) / total_valid * 100, 2)},
            },
            "strata_breakdown": strata_summary,
            "splits": {
                "train": sorted(train_paths),
                "val": sorted(val_paths),
                "test": sorted(test_paths),
            },
        }
