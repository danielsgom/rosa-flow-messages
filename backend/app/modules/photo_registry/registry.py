import json
import random
import re
from pathlib import Path
from typing import List, Optional

from app.modules.logger import get_logger
from .models import PhotoMeta

logger = get_logger(__name__)

_SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_META_FILE = "photos_meta.json"


class PhotoRegistry:
    """Manages the pool of photos available for sending."""

    def __init__(self, photos_dir: Path):
        self.photos_dir = photos_dir
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self._meta: dict[str, dict] = self._load_meta()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_photos(self) -> list[PhotoMeta]:
        """Return all photos with their metadata."""
        result = []
        for path in sorted(self.photos_dir.iterdir()):
            if path.name == _META_FILE or path.suffix.lower() not in _ALLOWED_EXTENSIONS:
                continue
            entry = self._meta.get(path.name, {"enabled": True})
            result.append(PhotoMeta(
                filename=path.name,
                size_bytes=path.stat().st_size,
                enabled=entry.get("enabled", True),
                url=f"/api/photos/{path.name}/file",
                caption=entry.get("caption") or None,
            ))
        return result

    def get_random_enabled_photo(
        self,
        exclude: Optional[List[str]] = None,
        allowed: Optional[List[str]] = None,
    ) -> Optional[Path]:
        """
        Return a random enabled photo path.
        allowed: if non-empty, only consider photos in this list (chat assignment).
        exclude: skip already-sent filenames this session.
        Falls back to any enabled photo if the filtered pool is empty.
        """
        exclude_set = set(exclude or [])
        allowed_set = set(allowed) if allowed else None

        def _pool(strict: bool) -> List[Path]:
            return [
                self.photos_dir / name
                for name, meta in self._meta.items()
                if meta.get("enabled", True)
                and (self.photos_dir / name).exists()
                and Path(name).suffix.lower() in _ALLOWED_EXTENSIONS
                and (not strict or name not in exclude_set)
                and (allowed_set is None or name in allowed_set)
            ]

        candidates = _pool(strict=True)
        if not candidates:
            # All assigned+enabled photos already sent → reset exclude constraint
            candidates = _pool(strict=False)
        if not candidates:
            return None
        return random.choice(candidates)

    def save_photo(self, filename: str, data: bytes) -> PhotoMeta:
        """Save a photo to disk and register it as enabled."""
        if not _SAFE_FILENAME_RE.match(filename):
            raise ValueError(f"Unsafe filename: {filename}")
        dest = self.photos_dir / filename
        dest.write_bytes(data)
        self._meta[filename] = {"enabled": True, "caption": None}
        self._save_meta()
        logger.info(f"Photo saved: {filename} ({len(data)} bytes)")
        return PhotoMeta(
            filename=filename,
            size_bytes=len(data),
            enabled=True,
            url=f"/api/photos/{filename}/file",
            caption=None,
        )

    def delete_photo(self, filename: str) -> bool:
        """Delete a photo from disk and metadata."""
        if not _SAFE_FILENAME_RE.match(filename):
            return False
        path = self.photos_dir / filename
        if not path.exists() or path.suffix.lower() not in _ALLOWED_EXTENSIONS:
            return False
        path.unlink()
        self._meta.pop(filename, None)
        self._save_meta()
        logger.info(f"Photo deleted: {filename}")
        return True

    def set_enabled(self, filename: str, enabled: bool) -> Optional[PhotoMeta]:
        """Enable or disable a photo for sending."""
        if not _SAFE_FILENAME_RE.match(filename):
            return None
        path = self.photos_dir / filename
        if not path.exists():
            return None
        entry = self._meta.get(filename, {})
        entry["enabled"] = enabled
        self._meta[filename] = entry
        self._save_meta()
        return PhotoMeta(
            filename=filename,
            size_bytes=path.stat().st_size,
            enabled=enabled,
            url=f"/api/photos/{filename}/file",
            caption=entry.get("caption") or None,
        )

    def set_caption(self, filename: str, caption: Optional[str]) -> Optional[PhotoMeta]:
        """Set or clear the caption for a photo."""
        if not _SAFE_FILENAME_RE.match(filename):
            return None
        path = self.photos_dir / filename
        if not path.exists():
            return None
        entry = self._meta.get(filename, {})
        entry["caption"] = caption or None
        self._meta[filename] = entry
        self._save_meta()
        return PhotoMeta(
            filename=filename,
            size_bytes=path.stat().st_size,
            enabled=entry.get("enabled", True),
            url=f"/api/photos/{filename}/file",
            caption=caption or None,
        )

    def get_caption(self, filename: str) -> Optional[str]:
        """Return the caption for a given filename, or None."""
        return self._meta.get(filename, {}).get("caption") or None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_meta(self) -> dict:
        meta_path = self.photos_dir / _META_FILE
        if not meta_path.exists():
            return {}
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"Failed to load photos_meta.json: {exc}")
            return {}

    def _save_meta(self) -> None:
        meta_path = self.photos_dir / _META_FILE
        meta_path.write_text(
            json.dumps(self._meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
