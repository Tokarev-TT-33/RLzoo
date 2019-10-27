"""
Vanilla Policy Gradient(VPG or REINFORCE)
-----------------------------------------
The policy gradient algorithm works by updating policy parameters via stochastic gradient ascent on policy performance.
It's an on-policy algorithm can be used for environments with either discrete or continuous action spaces.
Here is an example on discrete action space game CartPole-v0.
To apply it on continuous action space, you need to change the last softmax layer and the choose_action function.

Reference
---------
Cookbook: Barto A G, Sutton R S. Reinforcement Learning: An Introduction[J]. 1998.
MorvanZhou's tutorial page: https://morvanzhou.github.io/tutorials/

Prerequisites
--------------
tensorflow >=2.0.0a0
tensorflow-probability 0.6.0
tensorlayer >=2.0.0

"""
import time

import numpy as np

import gym
import tensorflow as tf
import tensorlayer as tl

from common.utils import *


###############################  PG  ####################################


class PG:
    """
    PG class
    """

    def __init__(self, net_list, optimizers_list):
        """
        :param net_list: a list of networks (value and policy) used in the algorithm, from common functions or customization
        :param optimizers_list: a list of optimizers for all networks and differentiable variables
        :param state_dim: dimension of state for the environment
        :param action_dim: dimension of action for the environment
        """
        assert len(net_list) == 1
        assert len(optimizers_list) == 1
        self.name = 'pg'
        self.model = net_list[0]
        self.buffer = []
        print('Policy Network', self.model)
        self.optimizer = optimizers_list[0]

    def choose_action(self, s):
        """
        choose action with probabilities.
        :param s: state
        :return: act
        """
        return self.model(np.array([s], np.float32))[0].numpy()

    def choose_action_greedy(self, s):
        """
        choose action with greedy policy
        :param s: state
        :return: act
        """
        return self.model(np.array([s], np.float32), greedy=True).numpy()[0]

    def store_transition(self, s, a, r):
        """
        store data in memory buffer
        :param s: state
        :param a: act
        :param r: reward
        :return:
        """
        self.buffer.append([np.array(s, np.float32), np.array(a, np.float32), np.array(r, np.float32)])

    def update(self, gamma):
        """
        update policy parameters via stochastic gradient ascent
        :return: None
        """
        # discount and normalize episode reward
        s, a, r = zip(*self.buffer)
        s, a, r = np.array(s), np.array(a), np.array(r).flatten()
        discounted_ep_rs_norm = self._discount_and_norm_rewards(r, gamma)

        with tf.GradientTape() as tape:
            self.model(np.vstack(s))
            neg_log_prob = self.model.policy_dist.neglogp(a)
            loss = tf.reduce_mean(neg_log_prob * discounted_ep_rs_norm)  # reward guided loss

        grad = tape.gradient(loss, self.model.trainable_weights)
        self.optimizer.apply_gradients(zip(grad, self.model.trainable_weights))

        self.buffer = []
        return discounted_ep_rs_norm

    def _discount_and_norm_rewards(self, reward_list, gamma):
        """
        compute discount_and_norm_rewards
        :return: discount_and_norm_rewards
        """
        # discount episode rewards
        discounted_ep_rs = np.zeros_like(reward_list)
        running_add = 0
        for t in reversed(range(0, len(reward_list))):
            running_add = running_add * gamma + reward_list[t]
            discounted_ep_rs[t] = running_add

        # normalize episode rewards
        discounted_ep_rs -= np.mean(discounted_ep_rs)
        discounted_ep_rs /= np.std(discounted_ep_rs)
        return discounted_ep_rs

    def save(self, name='policy'):
        """
        save trained weights
        :return: None
        """
        save_model(self.model, name, self.name)

    def load_ckpt(self, name='policy'):
        """
        load trained weights
        :return: None
        """
        load_model(self.model, name, self.name)

    def learn(self, env, train_episodes=300, test_episodes=200, max_steps=3000, save_interval=100,
              mode='train', render=False, gamma=0.95, seed=None):
        """
        parameters
        ----------
        :param env: learning environment
        :param train_episodes: total number of episodes for training
        :param test_episodes: total number of episodes for testing
        :param max_steps: maximum number of steps for one episode
        :param save_interval: timesteps for saving
        :param mode: train or test
        :param render: render each step
        :param gamma: reward decay
        :param seed: random seed
        :return: None
        """
        if seed:
            # reproducible
            np.random.seed(seed)
            tf.random.set_seed(seed)
            env.seed(seed)

        if mode == 'train':
            reward_buffer = []
            t0 = time.time()

            for i_episode in range(1, train_episodes + 1):

                observation = env.reset()

                ep_rs_sum = 0
                for step in range(max_steps):
                    if render:
                        env.render()

                    action = self.choose_action(observation)
                    observation_, reward, done, info = env.step(action)
                    self.store_transition(observation, action, reward)

                    ep_rs_sum += reward
                    observation = observation_

                    if done:
                        break

                try:
                    running_reward = running_reward * 0.99 + ep_rs_sum * 0.01
                except:
                    running_reward = ep_rs_sum

                print('Episode: {}/{}  | Episode Reward: {:.4f}  | Running Time: {:.4f}'.format(
                    i_episode, train_episodes, ep_rs_sum, time.time() - t0)
                )
                reward_buffer.append(running_reward)

                self.update(gamma)

                if i_episode and i_episode % save_interval == 0:
                    self.save()
            plot_save_log(reward_buffer, Algorithm_name='PG', Env_name=env.spec.id)

        elif mode == 'test':
            # test
            self.load_ckpt()
            t0 = time.time()
            for eps in range(test_episodes):
                observation = env.reset()
                ep_rs_sum = 0
                for step in range(max_steps):
                    if render:
                        env.render()
                    action = self.choose_action_greedy(observation)
                    observation, reward, done, info = env.step(action)
                    ep_rs_sum += reward
                    if done:
                        break
                try:
                    running_reward = running_reward * 0.99 + ep_rs_sum * 0.01
                except:
                    running_reward = ep_rs_sum
                print('Episode: {}/{}  | Episode Reward: {:.4f}  | Running Time: {:.4f}'.format(
                    eps, test_episodes, ep_rs_sum, time.time() - t0)
                )

        else:
            print('unknown mode type')
