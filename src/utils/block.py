"""
Block utility functions for Bitcoin-like block construction and hashing.
Includes serialization, coinbase transaction creation, and hash utilities.
"""
import hashlib
import struct
import base58

def encode_varint(i):
    """
    Encode an integer as a Bitcoin-style variable-length integer.
    Args:
        i (int): Integer to encode.
    Returns:
        bytes: Encoded varint.
    """
    if i < 0xfd:
        return i.to_bytes(1, 'little')
    elif i <= 0xffff:
        return b'\xfd' + i.to_bytes(2, 'little')
    elif i <= 0xffffffff:
        return b'\xfe' + i.to_bytes(4, 'little')
    else:
        return b'\xff' + i.to_bytes(8, 'little')

def encode_script_num(num):
    """
    Encode a number for use in Bitcoin script (BIP34).
    Args:
        num (int): Number to encode.
    Returns:
        bytes: Encoded number for scriptSig.
    """
    if num == 0:
        return b''
    result = bytearray()
    abs_num = abs(num)
    while abs_num:
        result.append(abs_num & 0xff)
        abs_num >>= 8
    if result[-1] & 0x80:
        result.append(0x80 if num < 0 else 0)
    elif num < 0:
        result[-1] |= 0x80
    return bytes(result)

def address_to_script_pubkey(address: str) -> bytes:
    """
    Convert a Base58Check Bitcoin address to a P2PKH scriptPubKey.
    Args:
        address (str): Base58Check Bitcoin address.
    Returns:
        bytes: ScriptPubKey for P2PKH.
    """
    decoded = base58.b58decode_check(address)
    pubkey_hash = decoded[1:]  # remove version byte (first byte)
    if len(pubkey_hash) != 20:
        raise ValueError("Invalid public key hash length")
    return b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'

def create_coinbase_tx(block_height: int, extra_nonce: int, miner_msg: str = "", address: str = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") -> bytes:
    """
    Create a serialized coinbase transaction for a new block.
    Args:
        block_height (int): Height of the block (for BIP34).
        extra_nonce (int): Extra nonce for uniqueness.
        miner_msg (str): Optional miner message for scriptSig.
    Returns:
        bytes: Raw serialized coinbase transaction.
    """
    version = struct.pack("<I", 1)
    tx_in_count = b'\x01'
    prev_out_hash = b'\x00' * 32
    prev_out_index = b'\xff\xff\xff\xff'
    height_bytes = encode_script_num(block_height)
    height_push = bytes([len(height_bytes)]) + height_bytes
    extra_data = struct.pack("<I", extra_nonce) + miner_msg.encode()
    script_sig = height_push + extra_data
    script_sig_len = encode_varint(len(script_sig))
    sequence = b'\xff\xff\xff\xff'
    tx_in = prev_out_hash + prev_out_index + script_sig_len + script_sig + sequence
    tx_out_count = b'\x01'
    value = struct.pack("<Q", 50 * 100_000_000)
    script_pubkey = address_to_script_pubkey(address) # not valid wallet address check P2PKH (Pay-to-PubKey-Hash) 
    script_pubkey_len = encode_varint(len(script_pubkey))
    tx_out = value + script_pubkey_len + script_pubkey
    lock_time = b'\x00\x00\x00\x00'
    raw_tx = version + tx_in_count + tx_in + tx_out_count + tx_out + lock_time
    return raw_tx

def txid(tx_bytes: bytes) -> str:
    """
    Compute the transaction ID (txid) as a double SHA256 hash of the transaction bytes.
    Args:
        tx_bytes (bytes): Raw transaction bytes.
    Returns:
        str: Transaction ID as a hex string (big-endian).
    """
    tx_hash = hashlib.sha256(hashlib.sha256(tx_bytes).digest()).digest()[::-1].hex()
    return tx_hash

def bits_to_target(bits):
    """
    Convert compact difficulty bits to a target integer.
    Args:
        bits (int): Compact representation of target.
    Returns:
        int: Target integer.
    """
    exponent = bits >> 24
    mantissa = bits & 0xffffff
    target = mantissa * (1 << (8 * (exponent - 3)))
    return target

def serialize_block_header(version, prev_hash, merkle_root, timestamp, bits, nonce):
    """
    Serialize block header fields into a 80-byte header.
    Args:
        version (int): Block version.
        prev_hash (str): Previous block hash (hex string).
        merkle_root (str): Merkle root (hex string).
        timestamp (int): Block timestamp.
        bits (int): Difficulty bits.
        nonce (int): Nonce value.
    Returns:
        bytes: Serialized block header.
    """
    header = b''
    header += struct.pack("<L", version)
    header += bytes.fromhex(prev_hash)[::-1]
    header += bytes.fromhex(merkle_root)[::-1]
    header += struct.pack("<L", timestamp)
    header += struct.pack("<L", bits)
    header += struct.pack("<L", nonce)
    return header

def double_sha256(data):
    """
    Compute SHA256(SHA256(data)).
    Args:
        data (bytes): Input data.
    Returns:
        bytes: Double SHA256 hash.
    """
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def compute_hash(header_fields):
    """
    Compute the block hash from header fields.
    Args:
        header_fields (dict): Block header fields.
    Returns:
        str: Block hash as a hex string (big-endian).
    """
    serialized = serialize_block_header(
        header_fields['version'],
        header_fields['previousblockhash'],
        header_fields['merkleroot'],
        header_fields['timestamp'],
        header_fields['bits'],
        header_fields['nonce']
    )
    hash_val = double_sha256(serialized)[::-1].hex()
    return hash_val 