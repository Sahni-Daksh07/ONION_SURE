"""
Grading Policy Registry and Loader

Centralizes policy management, dynamic discovery, and hot-swapping:
- Loads versioned JSON policies from config/grading_policies/
- Eliminates hardcoded magic thresholds in code
- Provides immutable policy version retrieval for audit trails
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .models import GradingPolicy

DEFAULT_POLICIES_DIR = Path("config") / "grading_policies"


class PolicyRegistry:
    """Registry maintaining active and historical grading policy versions."""

    def __init__(self, policies_dir: Path = DEFAULT_POLICIES_DIR):
        self.policies_dir = policies_dir
        self._policies: Dict[str, GradingPolicy] = {}
        self.reload_policies()

    def reload_policies(self) -> None:
        """Discovers and reloads all JSON policy files from the policies directory."""
        self._policies.clear()
        
        # Always register fallback default v1.0.0
        default_p = GradingPolicy()
        self._policies[default_p.version] = default_p

        if self.policies_dir.exists():
            for file in self.policies_dir.glob("*.json"):
                try:
                    p = GradingPolicy.from_json_file(file)
                    self._policies[p.version] = p
                except Exception as e:
                    print(f"Warning: Failed to load policy from {file}: {e}")

    def get_policy(self, version: str) -> GradingPolicy:
        """Retrieves a specific policy version. Raises KeyError if not found."""
        if version in self._policies:
            return self._policies[version]
        raise KeyError(
            f"Policy version '{version}' not found in registry. "
            f"Available versions: {list(self._policies.keys())}"
        )

    def get_default_policy(self) -> GradingPolicy:
        """Returns standard policy v1.0.0."""
        return self._policies.get("1.0.0", GradingPolicy())

    def list_policies(self) -> List[Dict[str, str]]:
        """Returns overview of all available policy versions."""
        return [
            {
                "version": p.version,
                "name": p.name,
                "effective_date": p.effective_date,
                "description": p.description,
            }
            for p in self._policies.values()
        ]

    def register_policy(self, policy: GradingPolicy) -> None:
        """Registers a policy in-memory."""
        self._policies[policy.version] = policy


# Global singleton registry
policy_registry = PolicyRegistry()
