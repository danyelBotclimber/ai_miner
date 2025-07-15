"""
Environment module for a simplified Bitcoin mining simulation using OpenAI Gym.
Defines the SimpleBitcoinEnv class and transaction generation utilities.
"""
import gym
import numpy as np
from gym import spaces
from src.config.constants import VERSION, PREVIOUS_BLOCK_HASH, BITS, BASE_TIMESTAMP, TRANSACTIONS
from src.utils.block import bits_to_target, compute_hash, create_coinbase_tx, txid
from src.utils.merkle import merkle_root
import time
import os
import random
import logging
from src.config.settings import ENABLE_LOGGING

if ENABLE_LOGGING:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
logger = logging.getLogger(__name__)

def generate_transactions(num_txs = random.randint(5, 1000)):
    """
    Generate a list of random transaction hashes for a new block.
    Args:
        num_txs (int): Number of transactions to generate (default: random between 5 and 1000).
    Returns:
        list[str]: List of transaction hashes as hex strings.
    """
    txs = [os.urandom(32).hex() for _ in range(num_txs)]
    if ENABLE_LOGGING:
        logger.info(f"Generated {num_txs} transactions for new block.")
    return txs

class SimpleBitcoinEnv(gym.Env):
    """
    OpenAI Gym environment simulating a simplified Bitcoin mining process.
    The agent must find a valid block hash by choosing nonce, extra_nonce, and transaction order.
    """
    def __init__(self):
        """
        Initialize the environment, action/observation spaces, and block parameters.
        """
        super().__init__()
        self.version = VERSION
        self.previousblockhash = PREVIOUS_BLOCK_HASH
        self.bits = BITS
        self.base_timestamp = BASE_TIMESTAMP
        self.transactions = TRANSACTIONS
        self.num_txs = len(self.transactions)

        # Action space: choose nonce, extra_nonce, and permutation of transactions
        self.action_space = spaces.Dict({
            "nonce": spaces.Discrete(2**32),
            "extra_nonce": spaces.Discrete(2**32),
            "tx_order": spaces.MultiDiscrete([self.num_txs] * self.num_txs)
        })

        # Observation space: block header fields and transaction order
        self.observation_space = spaces.Dict({
            "version": spaces.Discrete(2**32),
            "previousblockhash": spaces.Box(low=0, high=255, shape=(32,), dtype=np.uint8),
            "bits": spaces.Discrete(2**32),
            "timestamp": spaces.Discrete(2**32),
            "nonce": spaces.Discrete(2**32),
            "tx_order": spaces.MultiDiscrete([self.num_txs] * self.num_txs)
        })

        self.target = bits_to_target(self.bits)

        self.current_nonce = 0
        self.current_timestamp = self.base_timestamp
        self.current_tx_order = list(range(self.num_txs))
        self.block_height = 1
        if ENABLE_LOGGING:
            logger.info("Environment initialized.")

    def fix_permutation(self, arr, n):
        """
        Ensure the transaction order is a valid permutation of n elements.
        Args:
            arr (list[int]): Proposed permutation.
            n (int): Number of elements.
        Returns:
            list[int]: Valid permutation of n elements.
        """
        seen = set()
        res = []
        for x in arr:
            if x not in seen and 0 <= x < n:
                res.append(x)
                seen.add(x)
        for x in range(n):
            if x not in seen:
                res.append(x)
        return res[:n]

    def step(self, action):
        """
        Take an action in the environment: try to mine a block with the given parameters.
        Args:
            action (dict): Contains 'nonce', 'extra_nonce', and 'tx_order'.
        Returns:
            tuple: (observation, reward, done, info)
        """
        if ENABLE_LOGGING:
            logger.debug(f"Action received: {action}")
        nonce = int(action["nonce"])
        extra_nonce = int(action["extra_nonce"])

        tx_order = action["tx_order"].tolist() if isinstance(action["tx_order"], np.ndarray) else action["tx_order"]
        tx_order = [min(max(0, i), self.num_txs - 1) for i in tx_order]
        tx_order = self.fix_permutation(tx_order, self.num_txs)

        new_timestamp = int(self.base_timestamp)
        if new_timestamp < self.base_timestamp:
            new_timestamp = self.base_timestamp

        # Create coinbase transaction and compute its txid
        raw_coinbase_tx = create_coinbase_tx(self.block_height, extra_nonce, miner_msg="Mining with RL")
        coinbase_tx = txid(raw_coinbase_tx)

        # Reorder transactions and build full transaction list
        reordered_txs = [self.transactions[i] for i in tx_order]
        full_tx_list = [coinbase_tx] + reordered_txs
        new_merkle_root = merkle_root(full_tx_list)

        # Build block header fields
        header_fields = {
            "version": self.version,
            "previousblockhash": self.previousblockhash,
            "merkleroot": new_merkle_root,
            "timestamp": new_timestamp,
            "bits": self.bits,
            "nonce": nonce
        }

        if ENABLE_LOGGING:
            logger.debug(f"Block header fields: {header_fields}")
        block_hash = compute_hash(header_fields)
        hash_int = int(block_hash, 16)
        if ENABLE_LOGGING:
            logger.info(f"Block hash: {block_hash}, Target: {self.target}")

        reward = 0
        done = False

        # Check if the block hash meets the target (valid block)
        if hash_int < self.target:
            reward = 100
            self.previousblockhash = block_hash
            self.block_height += 1
            if ENABLE_LOGGING:
                logger.info(f"Valid block found! Height: {self.block_height-1}, Hash: {block_hash}")
            # Generate new transactions for the next block
            self.transactions = generate_transactions()
            self.num_txs = len(self.transactions)
        else:
            reward = - (hash_int / 2**256)
            if ENABLE_LOGGING:
                logger.debug(f"Invalid block. Hash: {block_hash} >= Target: {self.target}")

        self.current_nonce = nonce
        self.current_timestamp = new_timestamp
        self.current_tx_order = tx_order

        return self._get_obs(), reward, done, {
            "block_hash": block_hash,
            "hash_int": hash_int,
            "target": self.target,
            "header_fields": header_fields,
            "coinbase_tx": coinbase_tx,
            "full_tx_list": full_tx_list
        }

    def reset(self):
        """
        Reset the environment to the initial state for a new episode.
        Returns:
            dict: Initial observation.
        """
        self.current_nonce = 0
        self.current_timestamp = self.base_timestamp
        self.current_tx_order = list(range(self.num_txs))
        self.block_height = 1
        self.previousblockhash = "00" * 32
        if ENABLE_LOGGING:
            logger.info("Environment reset. Block height set to 1, previousblockhash reset.")
        return self._get_obs()

    def _get_obs(self):
        """
        Construct the current observation for the agent.
        Returns:
            dict: Observation dictionary.
        """
        prev_hash_bytes = bytes.fromhex(self.previousblockhash)
        obs = {
            "version": self.version,
            "previousblockhash": np.frombuffer(prev_hash_bytes, dtype=np.uint8),
            "bits": self.bits,
            "timestamp": self.current_timestamp,
            "nonce": self.current_nonce,
            "tx_order": np.array(self.current_tx_order)
        }
        if ENABLE_LOGGING:
            logger.debug(f"Observation: {obs}")
        return obs

    def render(self, mode='human'):
        """
        Print the current block header and environment state to the log (if enabled).
        """
        if ENABLE_LOGGING:
            logger.info("Current Block Header:")
            logger.info(f"  Version: {self.version}")
            logger.info(f"  Previous Block Hash: {self.previousblockhash}")
            logger.info(f"  Bits (difficulty): {hex(self.bits)}")
            logger.info(f"  Timestamp: {self.current_timestamp}")
            logger.info(f"  Nonce: {self.current_nonce}")
            logger.info(f"  Transaction order (non-coinbase): {self.current_tx_order}")
            logger.info(f"  Block height: {self.block_height}") 