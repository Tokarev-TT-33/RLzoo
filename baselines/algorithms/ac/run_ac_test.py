import gym
# from common.env_wrappers import DummyVecEnv
from common.utils import make_env, set_seed
from algorithms.ac.ac import AC
from common.value_networks import *
from common.policy_networks import *
from common.env_wrappers import build_env

''' load environment '''

EnvName = 'ReachTarget'
EnvType = 'rlbench'
env = build_env(EnvName, EnvType)
obs_space = env.observation_space
act_space = env.action_space
print(obs_space)
# reproducible
seed = 2
set_seed(seed, env)

# env = DummyVecEnv([lambda: env])  # The algorithms require a vectorized/wrapped environment to run


''' build networks for the algorithm '''
num_hidden_layer = 1  # number of hidden layers for the networks
hidden_dim = 32  # dimension of hidden layers for the networks
with tf.name_scope('AC'):
    with tf.name_scope('Critic'):
        critic = MultiHeadValueNetwork(obs_space, hidden_dim_list=num_hidden_layer * [hidden_dim])
    with tf.name_scope('Actor'):
        actor = MultiHeadStochasticPolicyNetwork(obs_space, act_space, hidden_dim_list=num_hidden_layer * [hidden_dim],
                                        output_activation=tf.nn.tanh)
net_list = [actor, critic]

''' choose optimizers '''
a_lr, c_lr = 1e-4, 1e-2  # a_lr: learning rate of the actor; c_lr: learning rate of the critic
a_optimizer = tf.optimizers.Adam(a_lr)
c_optimizer = tf.optimizers.Adam(c_lr)
optimizers_list = [a_optimizer, c_optimizer]

model = AC(net_list, optimizers_list)
''' 
full list of arguments for the algorithm
----------------------------------------
net_list: a list of networks (value and policy) used in the algorithm, from common functions or customization
optimizers_list: a list of optimizers for all networks and differentiable variables
gamma: discounted factor of reward
action_range: scale of action values
'''

model.learn(env, train_episodes=500,  max_steps=200,
            save_interval=50, mode='train', render=False)
''' 
full list of parameters for training
---------------------------------------
env: learning environment
train_episodes:  total number of episodes for training
test_episodes:  total number of episodes for testing
max_steps:  maximum number of steps for one episode
save_interval: time steps for saving the weights and plotting the results
mode: 'train' or 'test'
render:  if true, visualize the environment
'''
model.learn(env, test_episodes=100, max_steps=200,  mode='test', render=True)