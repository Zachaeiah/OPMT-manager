import re
import hashlib
from collections import defaultdict
from BOM_manager import CATEGORY_MAP


class PartIDGenerator:
    """
    Improved Part ID generator

    Features:
    - Better name parsing (keeps meaningful numbers like M6X20)
    - Optional stable IDs (hash-based)
    - Cleaner category handling
    """

    def __init__(self, category_map=None, use_hash=False):
        self.category_map = category_map or CATEGORY_MAP
        self.counters = defaultdict(int)
        self.use_hash = use_hash

    # -------------------------
    def generate(self, part_name: str, category: str = None) -> str:
        cat_code = self._get_category_code(category, part_name)
        name_code = self._name_to_code(part_name)

        base = f"{cat_code}-{name_code}"

        # Option 1: deterministic hash (stable across runs)
        if self.use_hash:
            suffix = self._hash_suffix(base)
            return f"{base}-{suffix}"

        # Option 2: incremental (session-based)
        self.counters[base] += 1
        return f"{base}-{self.counters[base]:04d}"

    # -------------------------
    def _get_category_code(self, category, part_name):
        if category:
            return self.category_map.get(
                category.lower(),
                category[:3].upper()
            )

        name_lower = part_name.lower()

        # stricter match (whole word priority)
        for key, code in self.category_map.items():
            if key == "default":
                continue

            if re.search(rf"\b{re.escape(key)}\b", name_lower):
                return code

        return self.category_map["default"]

    # -------------------------
    def _name_to_code(self, name: str) -> str:
        """
        Improved encoding:
        - Keeps numeric specs together (M6X20)
        - Removes filler words
        - Limits length for readability
        """

        name = name.upper()

        # extract tokens
        tokens = re.findall(r"[A-Z]+|\d+", name)

        if not tokens:
            return "GEN"

        # merge patterns like M6 + X + 20 → M6X20
        merged = []
        i = 0
        while i < len(tokens):
            t = tokens[i]

            if i + 2 < len(tokens):
                if re.match(r"[A-Z]+\d*", tokens[i]) and tokens[i+1] == "X" and tokens[i+2].isdigit():
                    merged.append(tokens[i] + "X" + tokens[i+2])
                    i += 3
                    continue

            merged.append(t)
            i += 1

        # remove weak words
        blacklist = {"THE", "AND", "PART", "COMPONENT"}
        filtered = [t for t in merged if t not in blacklist]

        # limit size (avoid insane IDs)
        return "".join(filtered[:3])[:16]

    # -------------------------
    def _hash_suffix(self, text: str) -> str:
        """
        Stable 4-char suffix
        """
        return hashlib.md5(text.encode()).hexdigest()[:4].upper()