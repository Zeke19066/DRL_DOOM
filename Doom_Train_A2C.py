import os
import time
from datetime import datetime
from collections import deque
import numpy as np
import json
import pickle

from decorators import function_timer
from Doom_Agent import Agent

import Doom_Wrapper

'''
Notes:

Desireable Behaviors: Facing Enemies (Enemies in Frame), Active Movement, Correct Weapon,

When the agent is learning from a dataset, it can begin with a 100% fail rate and quickly get its initial bearings,
usually with forward as the first move it learns. This is because action choices do not affect later outcomes when using
an on-the-rails Supervised environment. An Unsupervised agent cannot succeed under the same conditions, or else it may
not encounter later positive rewards once it enters a low-reward state.

Every "Session" gets 3 lives.

Batch Mismatch: "Another user came across this bug before. If the number of the peptides is N, then if N % mini_batch_size == 0 or 1, there will be an error:
If N % mini_batch_size == 0, such as in your case N = 15 * x, then the last batch is an empty batch which pytorch cannot handle.
If N % mini_batch_size == 1, i.e. there is only one row in a matrix, then pytorch will treat it differently as a vector."

Learning Rates:
    1e-6 (0.000001) Classic Rate
    1e-7 (0.0000001) Slow Rate

    3e-4 (0.0003) learning rate too fast & unstable
    5e-4 (0.0005)

'''
class ModelTrain():

    def __init__(self):
        print('Initializing Training Model', end="")

        #Parameters
        self.params = { ## User Set Training Hyperperameters & Game Parameters
            ## Hyperparameters:
            'actor_learning_rate':5e-6, #5e-6, 9e-6, 1e-6, 5e-4
            'critic_learning_rate':9e-6, #5e-6, 9e-6, 1e-6, 5e-4
            'gamma': 0.98, #0.95; Discount Factor
            'tau': 0.98, #0.8, 0.65; Scaling parameter for GAE
            'beta':0.2, #0.01; Entropy coefficient; induces more random exploration
            'epsilon': 0.08, #0.1; parameter for Clipped Surrogate Objective
            'epochs': 3, #5; how many times do you want to learn from the data
            'number_of_iterations': 20000000,
            'mini_batch_size': 200, #5; Used for dataset learning.
            'num_local_steps': 800, #20; Used for dataset learning. total learning steps at learn time.

            ## Game Parameters
            'min_reward':-0.5, 'max_reward':0.5, #what the rewards are scaled to
            'reward_target': -1000, #sets a minimum reward to save. Can be overwritten by higher avg.
            'lives_limit':5, #how many lives per session.
            'learn_cycles_goal': 3000, #how many cycles before we learn; across multiple lives
            'total_frames_limit': 3000, #Agent will time out in n frames per game.
            'lap_time_limit': 120, #90; max time per lap before we reset.
            'failure_time_limit': 10, #15; how many seconds of consecutive negative rewards before reset?
            'reward_ratio_limit': 0.75, #0.75; limit of % wrong answers.
            }

        #Counters
        self.varz = { ## Initialize counters & ques.
            'learn_cycles_checkpoint':0,# cycle count last time we learned.
            'lives_remaining':0, #Lives remaining
            'iteration': 1,
            'game_count':1,
            'reward_que':deque(maxlen=10), #final reward will be a moving avg.
            'game_time':1, #tally of play time in seconds. Menu/reset does not count.

            'reward_performance':deque(maxlen=25),
            'reward_avg_performance': 1,
            'reward_standard_deviation': 0,
            'all_lives_reward':0, #reward across learning session
            'time_performance':deque(maxlen=25), #Both finish and non-finish races
            'time_avg_performance': 1,
            'time_finish_performance':deque(maxlen=25), #Only counts time of races fully completed (3 laps)
            'time_finish_avg_performance': 0,
            'agent_qmax_list': [],
            'agent_qmax_avg':0,
            'critic_qmax_list': [],
            'critic_qmax_avg':0,

            'dps_out_que':deque(maxlen=25),
            'dps_in_que':deque(maxlen=25),
            'kill_count_que':deque(maxlen=25),

            'reward_polarity': [0, 0],#positive count, negative count of rewards.
            'race_over_bool': False,
            'reset_bool':False,
            'parent_counter':1,
            #loss is permanent like win, fail is per 'session' and is reset
            'negative_reward_count': 0,
            }
        self.varz['lives_remaining'] = self.params['lives_limit']

        self.home_dir = os.getcwd()
        self.varz_path = r'pretrained_model\varz.pkl'

        ## Initialize the class variables:
        self.total_reward = 0
        self.subcycle = 0
        self.last_reset = 0
        self.shot_counter = 0
        self.race_time_delta = 0
        self.total_time = 0
        self.completion_bool = False
        self.subtime = 0
        self.image_data_ = 0
        self.np_action = 0

        self.cycles_per_second = "Initializing"
        self.file_name = ""
        self.home_dir = os.getcwd()

        print('... launching Wrapper', end="")
        self.game_wrapper = Doom_Wrapper.DoomGame(self.params['total_frames_limit'])
        self.game = self.game_wrapper.game
        self.action_set_permutations = self.game_wrapper.action_set_permutations
        num_actions = len(self.action_set_permutations)

        print('... launching Agent', end="")
        self.agent = Agent(self.params, num_actions) #give it the whole dict.
        print('... Initialization Complete.')

    #@function_timer
    def train(self, start, send_connection):
        """
        The main training function.
        """

        ## Store tracking variables.
        self.varz['reset_bool'] = False
        self.varz['race_over_bool'] = False
        self.total_reward, self.subcycle = 1, 0
        self.last_reset = self.varz['iteration']

        self.shot_counter, self.race_time_delta, self.total_time = 0, 0, 0
        terminal, self.learn_bool = False, False
        self.completion_bool, death_bool, game_over_bool = False, False, False
        skipset = [n for n in range(5)] #first 5 actions are movement.

        self.agent.initial_state_bool = True
        self.subtime = datetime.now()
        self.game = self.game_wrapper.game

        self.game.new_episode()#start a new session
        if self.game_wrapper.map == "MAP07": #Manual setup for mission.
            self.game.make_action(self.action_set_permutations[8]) # open door
        state = self.game.get_state()
        state_last = state

        ## Call to the screenshot & image-to-tensor methods.
        image_data = state.screen_buffer
        image_data = self.game_wrapper.resize(image_data)
        image_tensor = self.agent.image_to_tensor(image_data)

        ## Main cycle loop
        print('Entering Training Loop')

        while not self.game.is_episode_finished():

            self.subcycle = max(self.varz['iteration'] - self.last_reset, 1)
            action, prob, crit_val, action_space = self.agent.choose_action(image_tensor)

            ## Get qmax with decimal accuracy
            action_space *= 10 #fast decimal, allows int detachment with accuracy.
            #its faster if we turn it into ints.float32, int32
            action_space = action_space.detach().cpu().numpy().astype('int32') 
            #action_space = action_space/10#now get it back to the right decimal place.
            action_space = action_space[0]

            qmax = np.max(action_space)
            self.np_action = action

            ## Execute action
            self.game.make_action(self.action_set_permutations[self.np_action]) # Execute Action

            ## Get State
            state_ = self.game.get_state()
            try:
                if str(type(state_)) == "<class 'NoneType'>":
                    #print("NONE TYPE", qmax, crit_val)
                    state_ = state_last
                    death_bool = True
            except Exception as e:
                print(str(type(state_)), e)

            self.image_data_ = state_.screen_buffer
            ## Get meta
            #   the variables we are tracking.
            vars_set, label_set = state_.game_variables, state_.labels
            reward, terminal = self.game_wrapper.reward_rules(self.np_action,
                                                              vars_set,
                                                              self.subcycle,
                                                              death_bool,
                                                              label_set)
            if reward > 0:
                self.varz['reward_polarity'][0] += 1
            else:
                self.varz['reward_polarity'][1] += 1

            #print(state_.number, terminal)
            self.image_data_ = self.game_wrapper.resize(self.image_data_)
            image_tensor_ = self.agent.image_to_tensor(self.image_data_)

            #Theres always at least a random chance to remember
            if ((np.random.randint(4) == 0)
                    #or (self.np_action not in skipset)
                    or (abs(reward) > 1)
                    or terminal):
                self.agent.remember(image_tensor, action,
                                    prob, crit_val, reward,
                                    terminal)

            state_last = state_
            image_tensor = image_tensor_
            self.total_reward += reward

            self.varz['iteration'] += 1

            ## Multiprocessing pipe to send metrics to GUI
            self.varz['agent_qmax_list'].append(qmax)
            self.varz['agent_qmax_avg'] = round(np.mean(self.varz['agent_qmax_list']), 1)
            self.varz['critic_qmax_list'].append(crit_val)
            self.varz['critic_qmax_avg'] = round(np.mean(self.varz['critic_qmax_list']), 1)

            dmg_in = self.game_wrapper.vars_dict['DAMAGE_TAKEN']
            dmg_out = self.game_wrapper.vars_dict['DAMAGECOUNT']
            kill_count = self.game_wrapper.vars_dict['KILLCOUNT']
            dps_in = round(dmg_in/self.race_time_delta, 1)
            dps_out = round(dmg_out/self.race_time_delta, 1)
            if terminal:
                self.varz['dps_in_que'].append(dps_in)
                self.varz['dps_out_que'].append(dps_out)
                self.varz['kill_count_que'].append(kill_count)
                print(f"DPSI: {dps_in}/{np.mean(self.varz['dps_in_que'])}")
                print(f"DPSO: {dps_out}/{np.mean(self.varz['dps_out_que'])}")
                print(f"Kill Count: {kill_count}/{np.mean(self.varz['kill_count_que'])}")
            dps_in_avg = np.mean(self.varz['dps_in_que'])
            dps_out_avg = np.mean(self.varz['dps_in_que'])
            kill_count_avg = np.mean(self.varz['kill_count_que'])

            dmg_list = [dmg_in,
                        dmg_out,
                        dps_in,
                        dps_out,
                        dps_in_avg,
                        dps_out_avg
                        ]
            action = np.argmax(action_space)
            if self.subcycle % 5 == 0: #time calcs are costly, so we limit them
                self.total_time = int((datetime.now() - start).total_seconds())
                #type(time_delta) = Float
                self.race_time_delta = (datetime.now() - self.subtime).total_seconds()

            try:
                metrics = [ #Game Metrics
                    action, reward,                                     #0-1
                    [action_space], self.total_reward, self.subcycle,   #2-4
                    99999,                                              #5
                    self.varz['iteration'], self.total_time, qmax,      #6-8
                    self.varz['reward_polarity'],                       #9
                    999999,                                             #10
                    int(crit_val), self.cycles_per_second,              #11-12
                    self.varz['agent_qmax_avg'],                        #13
                    self.params['actor_learning_rate'],                 #14
                    self.varz['game_time'],                             #15
                    self.varz['critic_qmax_avg'],                       #16
                    self.race_time_delta,                               #17
                    self.params['mini_batch_size'], dmg_list,           #18-19
                    self.varz['game_count'],                            #20
                    self.varz['reward_avg_performance'],                #21
                    ]

                self.gui_send(send_connection, metrics)
            except Exception as e: 
                print("Send Failure:", e) #print out if GUI not operating.

            p_bool = False #performance bool
            if terminal:#Game is saying we died
                self.varz['lives_remaining'] -= 1
                #terminal = False
                game_over_bool = True
                p_bool = ((self.varz['dps_in_que'][-1] < dps_in_avg)
                          or (self.varz['kill_count_que'][-1] > kill_count_avg))
                if not p_bool:
                    self.agent.memory.clear_memory()

            ## Determine Learning
            learn_delta = self.varz['iteration'] - self.varz['learn_cycles_checkpoint']

            if p_bool:
                    #terminal
                    #and (self.varz['lives_remaining'] <= 0)
                    #and (learn_delta >= self.params['learn_cycles_goal'])):

                self.varz['lives_remaining'] = self.params['lives_limit']
                self.learn_bool = True
                terminal = True 
                game_over_bool = True

            ## Trigger reset; GAME OVER
            if game_over_bool:
                self.training_reset() #learning happens here
                return #this will kick us back into the main function below and restart training.

    # Testing Environment
    def test(self, start, send_connection):
        pass

    def training_reset(self):
        """
        Reset protocol for training.
        """
        self.varz['game_time'] += int(self.race_time_delta)
        #pesky divide by zero.
        self.cycles_per_second = round(self.subcycle/max(self.race_time_delta, 1), 2)

        self.varz['all_lives_reward'] += self.total_reward

        if self.learn_bool:
            if self.varz['parent_counter'] != 6 or 1==1: #Bypass
                print("Learning...", end="")
                self.agent.learn() #we learn once the race is over.
                self.varz['learn_cycles_checkpoint'] = self.varz['iteration']

        #self.agent.memory.clear_memory()

        self.varz['game_count'] += 1
        self.varz['reward_performance'].append(self.total_reward)
        self.varz['reward_avg_performance'] = round(np.mean(self.varz['reward_performance']), 2)
        self.varz['reward_standard_deviation'] = round(np.std(self.varz['reward_performance']), 2)
        self.varz['time_performance'].append(self.race_time_delta)
        self.varz['time_avg_performance'] = round(np.mean(self.varz['time_performance']), 1)
        if self.completion_bool: #we finished the race
            self.varz['time_finish_performance'].append(self.race_time_delta)
            val = round(np.mean(self.varz['time_finish_performance']), 1)
            self.varz['time_finish_avg_performance'] = val

        self.varz['agent_qmax_list'], self.varz['critic_qmax_list'] = [], []
        self.varz['reward_polarity'] = [0, 0]
        self.varz['current_lap'], self.varz['current_lap_time'] = 1, 0
        self.varz['lap_time_dict'] = {1:0, 2:0, 3:0}

        self.varz['final_reward_score'] = self.total_reward
        self.varz['back_on_track_bonus'] = 0
        self.varz['negative_reward_count'] = 0
        self.last_reset = self.varz['iteration']
        self.subtime = datetime.now()

        self.game_wrapper.wrapper_reset()

        if self.varz['parent_counter'] == 6 and 1 != 1: #Bypass
            self.varz['parent_counter'] = 1 #reset the counter
            self.agent.merge_models()
        #elif self.varz['parent_counter'] != 6 and self.learn_bool:
        elif self.learn_bool:
            self.agent.save_models()

    def logger(self, mode):
        """
        Handles file logging.
        mode: save/load

        Loading is done through update, so new entries
        in varz are not erased when an older dict is loaded
        """
        os.chdir(self.home_dir)

        if mode == 'save':
            ##Save Counters Pickle
            with open(self.varz_path, 'wb') as outp:
                pickle.dump(self.varz, outp, pickle.HIGHEST_PROTOCOL)

        elif mode == 'load':
            print('Loading Counters Pickle', end="")

            if os.path.exists(self.varz_path):
                with open(self.varz_path, 'rb') as inp:
                    varz_temp = pickle.load(inp)
                    self.varz.update(varz_temp)
 
                    print('...done', end="")

            elif not os.path.exists(self.varz_path):
                print(f"No Pickle Avalable at {self.varz_path}")

            self.varz['hist_time'] = self.varz['total_time']

    # A method for communicating with the GUI through Multiprocess Pipe
    def gui_send(self, conn, metrics):
        #conn.close()
        metrics.append(-9999) # just some fodder to signal the end of the transmission.
        for metric in metrics:
            conn.send(metric)

# Script initialization switchboard
def main(mode, send_connection=False):

    if mode == 'train':
        start = datetime.now()
        choo_choo = ModelTrain()
        choo_choo.train(start, send_connection)
        while 1:
            choo_choo.train(start, send_connection)

    elif mode == 'test':
        start = datetime.now()
        proctor = ModelTrain()
        proctor.test(start, send_connection)
        while 1:
            proctor.test(start, send_connection)

if __name__ == "__main__":
    main('train')
