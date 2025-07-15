"""
Constants for the Bitcoin mining environment.
Defines block version, previous block hash, difficulty bits, base timestamp, and initial transactions.
"""
import time

VERSION = 0x20000000  # Block version (fixed for this simulation)
PREVIOUS_BLOCK_HASH = "00" * 32  # Placeholder for previous block hash (all zeros)
BITS = 0x1f7fffff  # Difficulty bits (low difficulty for simulation)
BASE_TIMESTAMP = int(time.time())  # Unix timestamp for the base block
TRANSACTIONS = [
    # Example transaction hashes (hex strings)
    "27a1ed6ac1abbc3298f5c593c4b236d3360602e3d973f2e2eae78ae8ebb00eef",
    "d10c02cf8eb0e9ea32a037e0bc3a7290958ce00ca39e8162a221a0c59e8592d8",
    "d5323c5921a64e2ef7ee61f09400811b4ce501b37c0e0eb062d391280000749e",
    "9e4ab9d29f3178bc90333944cdfd9bdfc9b1ed36b5519566b64b06b0e5f6c6cd",
    "55adb58a31be1fa5bebad8a23e34035d3da781ea5a3fbcbb610bd629be3eb3d4",
    "c5b3e91ff5a90e35003c35ab34b866e09a05f411b9c16583d61eed57e7b62a30",
    "83e4dde10315507d5387f22f5a7b9d4d41cd57989aa9ecbc7accd1e91bd99128",
] 