"""
Optional one-shot script to (re)build the Chroma collection.
Not required at runtime — main path auto-creates on first empty query.
"""

from tools.semantic import get_or_create_collection
from utils.logger import get_logger

_logs = get_logger(__name__)

if __name__ == "__main__":
    col = get_or_create_collection()
    _logs.info(f"Collection ready. Document count = {col.count()}")
