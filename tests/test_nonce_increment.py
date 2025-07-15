import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from environments.simple_bitcoin_env import SimpleBitcoinEnv
import numpy as np

NUM_BLOCKS_TO_FIND = 3  # Set how many valid blocks to find before stopping

if __name__ == "__main__":
    env = SimpleBitcoinEnv()
    obs = env.reset()
    print("Initial Observation:", obs)

    blocks_found = 0
    total_steps = 0
    extra_nonce = 0
    tx_order = np.arange(env.num_txs)  # fixed order

    while blocks_found < NUM_BLOCKS_TO_FIND:
        for nonce in range(0, 2**32):
            action = {
                "nonce": nonce,
                "extra_nonce": extra_nonce,
                "tx_order": tx_order
            }
            obs, reward, done, info = env.step(action)
            total_steps += 1

            if total_steps % 10000 == 0:
                print(f"Step {total_steps}: Nonce {nonce}, Hash {info['block_hash']} Reward: {reward}")

            if reward > 0:
                blocks_found += 1
                print(f"✅ Valid block #{blocks_found} found after {total_steps} steps!")
                print(f"Nonce: {nonce}")
                print(f"Block Hash: {info['block_hash']}")
                print(f"Block Header Fields: {info['header_fields']}")
                #obs = env.reset()
                break
        else:
            print("No valid hash found in nonce range for this block.")
            obs = env.reset()

    print(f"Finished! Found {blocks_found} valid blocks in {total_steps} total steps.") 