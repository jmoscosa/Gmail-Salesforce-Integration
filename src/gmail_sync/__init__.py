"""gmail_sync package initialization."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("gmail-salesforce-sync")
except PackageNotFoundError:
    __version__ = "unknown"