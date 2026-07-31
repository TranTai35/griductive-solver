import hashlib
import random
from pathlib import Path

import pygame


class AvatarManager:
    """Assigns unique avatars per board and caches scaled Pygame surfaces."""

    def __init__(self, puzzle_id, cells):
        project_root = Path(__file__).resolve().parents[1]
        avatar_dir = project_root / "assets" / "sprites" / "avatars"
        paths = sorted(
            avatar_dir.glob("*.png"),
            key=lambda path: (not path.stem.isdigit(), int(path.stem) if path.stem.isdigit() else path.stem),
        )
        if len(paths) < len(cells):
            raise ValueError(
                f"Not enough avatars: the board needs {len(cells)}, "
                f"but only {len(paths)} PNG files exist in {avatar_dir}"
            )

        ordered_cells = sorted(cells, key=lambda cell: (int(cell[1:]), cell[0]))
        seed = int.from_bytes(
            hashlib.sha256(str(puzzle_id).encode("utf-8")).digest()[:8],
            "big",
        )
        random.Random(seed).shuffle(paths)
        self.avatar_paths = dict(zip(ordered_cells, paths))
        self._source_cache = {}
        self._scaled_cache = {}

    def path_for(self, cell):
        return self.avatar_paths[cell]

    def get(self, cell, max_size):
        """Return a proportionally scaled avatar that fits max_size."""
        max_width, max_height = max(1, int(max_size[0])), max(1, int(max_size[1]))
        cache_key = (cell, max_width, max_height)
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]

        path = self.avatar_paths[cell]
        source = self._source_cache.get(path)
        if source is None:
            source = pygame.image.load(str(path)).convert_alpha()
            self._source_cache[path] = source

        width, height = source.get_size()
        ratio = min(max_width / width, max_height / height)
        target_size = (
            max(1, round(width * ratio)),
            max(1, round(height * ratio)),
        )
        scaled = pygame.transform.smoothscale(source, target_size)
        self._scaled_cache[cache_key] = scaled
        return scaled

