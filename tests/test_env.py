import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from environments.simple_bitcoin_env import SimpleBitcoinEnv
import numpy as np

if __name__ == "__main__":
    env = SimpleBitcoinEnv()
    obs = env.reset()
    print("Initial Observation:", obs)

    done = False
    step_count = 0

    while not done:
        random_action = {
            "nonce": env.action_space["nonce"].sample(),
            "extra_nonce": env.action_space["extra_nonce"].sample(),
            "tx_order": np.random.permutation(env.num_txs)
        }
        obs, reward, done, info = env.step(random_action)
        step_count += 1

        if step_count % 1000 == 0:
            print(f"Step {step_count}: Current hash {info['block_hash']} Reward: {reward}")

    print(f"✅ Valid hash found after {step_count} steps!")
    print(f"Block Hash: {info['block_hash']}")
    print(f"Block Header Fields: {info['header_fields']}") 