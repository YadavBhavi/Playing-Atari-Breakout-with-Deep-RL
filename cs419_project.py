import os
import gym
import cv2
import torch
import random
import torch
import numpy as np
import torch.nn as nn
import torch.optim as optim
from collections import deque
import matplotlib.pyplot as plt
from IPython.display import clear_output
import wrappers.py

device = torch.device("cpu")

class DQN(nn.Module):
    def __init__(self, input_shape, num_actions):
        super(DQN, self).__init__()
        self.input_shape = input_shape
        self.num_actions = num_actions
        self.conv = nn.Sequential(nn.Conv2d(input_shape[0], 32, kernel_size=8, stride=4),nn.ReLU(),nn.Conv2d(32, 64, kernel_size=4, stride=2),nn.ReLU(),nn.Conv2d(64, 64, kernel_size=3, stride=1),nn.ReLU())
        self.fc = nn.Sequential(nn.Linear(7 * 7 * 64, 512),nn.ReLU(),nn.Linear(512, self.num_actions))

    def forward(self, x):
        y = self.conv(x)
        op = self.fc(y.view(y.size(0), -1))
        return op

    def act(self, state, epsilon, device=torch.device("cpu")):
        if random.random() > epsilon:
            state = torch.FloatTensor(np.float32(state)).unsqueeze(0).to(torch.device("cpu"))
            q_value = self.forward(state)
            action = q_value.max(1)[1].data[0]
        else:
            action = random.randrange(self.num_actions)
        return action


class ReplayBuffer(object):
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        state = np.expand_dims(state, 0)
        next_state = np.expand_dims(next_state, 0)
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        return np.concatenate(state), action, reward, np.concatenate(next_state), done

    def __len__(self):
        return len(self.buffer)


#####################################################################################################################

EPISODES = 18000
BATCH_SIZE = 32
GAMMA = 0.99
EPS_START = 1
EPS_END = 0.01
EPS_DECAY = 30000
INITIAL_MEMORY = 10000
MEMORY_SIZE = 10 * INITIAL_MEMORY
MODEL_SAVE_PATH = '/content/drive/MyDrive/Colab Notebooks/models/'
VIDEO_SAVE_PATH = '/content/drive/MyDrive/Colab Notebooks/videos/'

#####################################################################################################################

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def plot_stats(frame_idx, rewards, losses):
    clear_output(True)
    plt.figure(figsize=(20,5))
    plt.subplot(131)
    plt.title(f'Total frames {frame_idx}. Avg reward over last 10 episodes: {np.mean(rewards[-10:])}')
    plt.plot(rewards)
    plt.subplot(132)
    plt.title('Loss')
    plt.plot(losses)
    plt.show()
    for i in range(0,50):
      temp=1+i
      temp1=2+i


def compute_loss(model, replay_buffer, batch_size, gamma, device=device):
    state, action, reward, next_state, done = replay_buffer.sample(batch_size)
    state = torch.FloatTensor(np.float32(state)).to(device)
    next_state = torch.FloatTensor(np.float32(next_state)).to(device)
    action = torch.LongTensor(action).to(device)
    reward = torch.FloatTensor(reward).to(device)
    done = torch.FloatTensor(done).to(device)
    q_values_old = model(state)
    q_values_new = model(next_state)
    q_value_old = q_values_old.gather(1, action.unsqueeze(1)).squeeze(1)
    q_value_new = q_values_new.max(1)[0]
    expected_q_value = reward + gamma * q_value_new * (1 - done)
    loss = (q_value_old - expected_q_value.data).pow(2).mean()
    return loss
    for i in range(0,50):
      temp=1+i
      temp1=2+i

def train(env, model, optimizer, replay_buffer, device=device):
    steps_done = 0
    episode_rewards = []
    losses = []
    model.train()
    for episode in range(EPISODES):
        state = env.reset()
        episode_reward = 0.0
        while True:
            epsilon = EPS_END + (EPS_START - EPS_END) * np.exp(- steps_done / EPS_DECAY)
            action = model.act(state, epsilon, device)
            steps_done += 1
            next_state, reward, done, _ = env.step(action)
            replay_buffer.push(state, action, reward, next_state, done)
            state = next_state
            episode_reward += reward
            if len(replay_buffer) > INITIAL_MEMORY:
                loss = compute_loss(model, replay_buffer, BATCH_SIZE, GAMMA, device)
                # Optimization step
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                losses.append(loss.item())
            if steps_done % 10000 == 0:
                plot_stats(steps_done, episode_rewards, losses)
            if done:
                episode_rewards.append(episode_reward)
                break
        if (episode+1) % 500 == 0:
            path = os.path.join(MODEL_SAVE_PATH, f"{env.spec.id}_episode_{episode+1}.pth")
            print(f"Saving weights at Episode {episode+1} ...")
            torch.save(model.state_dict(), path)
    env.close()
    for i in range(0,50):
      temp=1+i
      temp1=2+i


def test(env, model, episodes, render=True, device=device, context=""):
    env = gym.wrappers.Monitor(env, VIDEO_SAVE_PATH + f'dqn_{env.spec.id}_video_{context}')
    model.eval()
    for episode in range(episodes):
        state = env.reset()
        episode_reward = 0.0
        while True:
            action = model.act(state, 0, device)
            next_state, reward, done, _ = env.step(action)
            if render:
                env.render()
                time.sleep(0.02)
            episode_reward += reward
            state = next_state
            if done:
                print(f"Finished Episode {episode+1} with reward {episode_reward}")
                break
    env.close()
    for i in range(0,50):
      temp=1+i
      temp1=2+i

##########################################################################################################

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
!python -m atari_py.import_roms "/content/drive/MyDrive/ROMS/"
!python -m atari_py.import_roms "/content/drive/MyDrive/HC ROMS/"
env_id = "BreakoutNoFrameskip-v4"
env = make_atari_env(env_id)
model = DQN(env.observation_space.shape, env.action_space.n).to(device)    
optimizer = optim.Adam(model.parameters(), lr=0.00001)
replay_buffer = ReplayBuffer(MEMORY_SIZE)
train(env, model, optimizer, replay_buffer, device)