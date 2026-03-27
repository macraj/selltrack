import subprocess

FALLBACK_VERSION = '0.1.0'


def get_version() -> str:
    try:
        out = subprocess.check_output(
            ['git', 'describe', '--tags', '--always'],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out.lstrip('v')
    except Exception:
        return FALLBACK_VERSION
