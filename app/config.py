import os

from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("VALO_REGION", "na")
MOCK = os.getenv("VALO_MOCK", "1") == "1"
RECENT_MATCHES = int(os.getenv("VALO_RECENT", "10"))


def apply_runtime_settings(region=None, mock=None):
	"""Allow desktop/UI controls to update runtime behavior without restart."""
	global REGION, MOCK
	if region is not None:
		REGION = str(region).strip().lower() or REGION
	if mock is not None:
		MOCK = bool(mock)
