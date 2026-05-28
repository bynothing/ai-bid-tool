"""Project type profiles for bid-tool pipeline configuration."""
import yaml
from pathlib import Path

PROFILES_DIR = Path(__file__).resolve().parent


def load_profile(profile_name: str) -> dict:
    """Load a project type profile by name (without .yaml extension)."""
    profile_path = PROFILES_DIR / f"{profile_name}.yaml"
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    with open(profile_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def list_profiles() -> list[str]:
    """List available profile names."""
    return [p.stem for p in PROFILES_DIR.glob("*.yaml")]
