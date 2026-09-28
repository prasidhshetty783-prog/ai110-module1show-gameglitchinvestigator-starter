"""Put the project root on sys.path so tests can `import logic_utils`.

Without this, pytest inserts only the `tests/` directory and the import fails.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
