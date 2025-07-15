"""
Merkle tree utilities for computing the Merkle root of a list of transaction hashes.
"""
import hashlib

def double_sha256(data: bytes) -> bytes:
    """
    Compute SHA256(SHA256(data)).
    Args:
        data (bytes): Input data.
    Returns:
        bytes: Double SHA256 hash.
    """
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def merkle_root(tx_hashes):
    """
    Compute the Merkle root of a list of transaction hashes.
    Args:
        tx_hashes (list[str]): List of transaction hashes as hex strings.
    Returns:
        str: Merkle root as a hex string (big-endian).
    """
    if len(tx_hashes) == 0:
        return '00' * 32
    hashes = [bytes.fromhex(h) for h in tx_hashes]
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        new_hashes = []
        for i in range(0, len(hashes), 2):
            new_hashes.append(double_sha256(hashes[i] + hashes[i+1]))
        hashes = new_hashes
    merkle = hashes[0][::-1].hex()
    return merkle 