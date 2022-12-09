#####################################################################
# This script presents how to use the most basic features of the environment.
# It configures the engine, and makes the agent perform random actions.
# It also gets current state and reward earned with the action.
# <episodes> number of episodes are played.
# Random combination of buttons is chosen for every action.
# Game variables from state and last reward are printed.
#
# To see the scenario description go to "../../scenarios/README.md"
#####################################################################

import os
import itertools as it
from random import choice #returns a random element from a list.
from time import sleep
from collections import deque

from decorators import function_timer
import cv2
import numpy as np
import vizdoom as vzd


#Somehow the delta button example actualy loads level 1

class DoomGame():
    """A Wrapper for vizdoom"""
    def __init__(self, total_frame_limit):
        self.window_show_bool = True #Does not affect framerate.
        self.xy = 126  #downsize to 126x126px
        self.scenario_bool = False
        self.map = "MAP07" #2,7,15,21,23
        self.scenario_path = "defend_the_center.cfg"
        self.turn_delta = 2.5 #how many degrees per turn
        self.difficulty = 1 #1-5; default 3
        #will reset if we havent finished by n frames.
        self.total_frame_limit = total_frame_limit
        self.hit_bonus = 5 #reward spillover

        #The reward bonuses. += unless otherwise noted.
        self.r_rules = {
            'passive': -0.25,
            'spillover': 5, #overwrites
            'enemy_screen': 0.25,
            'scored_kill': 30,
            'died': -10, #overwrites
            'dmg_out_min': 4,
            'dmg_out_max': 6,
            'dmg_in_min': 4,
            'dmg_in_max': 8,
            'stuck': -2,
            'stuck_timeout': -18,#overwrites
            'dry_fire':-1, #attacked without enemy on screen.
        }

        self.scored_kill = False
        self.w_varz = { #Wrapper Counters
            'reward_que': deque(maxlen=10),
            'dmg_out_que': deque([1], maxlen=25),
            'dmg_in_que': deque([1], maxlen=25),
            'hit_spillover':0,
            'stuck_counter':0, #how many frames with no x/y delta
            'enemy_names':["Fatso", "Zombieman",
                           "MarineChainsawVzd", "Demon"],
            'sum_dmg_out':0,
            'sum_dmg_in':0,
        }
        self.vars_dict_last = ""
        self.game_init() #run the initialization function.

    def game_init(self):
        """Subinit for the game settings; allows seperate resetting"""
        #for when you only allow one button at a time.
        def single_button_permutations(length):
            blank = [0 for n in range(length)] #create zeros.
            out_list = []
            for n in range(length):
                mask = blank.copy()
                mask[n] = 1
                out_list.append(mask)

            # add in the fast mode for the movement buttons
            # This "fast button" needs to be pressed at the
            # same time as a movement key.
            for i in range(length):
                if i < 4:
                    out_list[i].append(1)
                else:
                    out_list[i].append(0)

            out_list[4][4] = -1*self.turn_delta #left delta in degrees
            right_delta = out_list[4].copy() #Copy the left, but make it a positive value.
            right_delta[4] = self.turn_delta
            out_list.insert(5, right_delta) #now insert it after the left delta.

            self.action_set.append(vzd.Button.SPEED) #and then add the speed overwrite
            return out_list

        # Create DoomGame instance. It will run the game and communicate with you.
        self.game = vzd.DoomGame()
        self.action_set = [ # All the moves the agent can make (10x)
            vzd.Button.MOVE_FORWARD,            #0
            vzd.Button.MOVE_BACKWARD,           #1
            vzd.Button.MOVE_LEFT,               #2
            vzd.Button.MOVE_RIGHT,              #3
            vzd.Button.TURN_LEFT_RIGHT_DELTA,   #4
            vzd.Button.ATTACK,                  #5
            vzd.Button.SELECT_NEXT_WEAPON,      #6
            vzd.Button.USE,                     #7
            vzd.Button.JUMP, #Controversial     #8
            ]
        self.action_set_permutations = []
        self.variables_set = [ #The variables we will be tracking in the session
            vzd.GameVariable.KILLCOUNT,
            vzd.GameVariable.DEATHCOUNT,
            vzd.GameVariable.HITCOUNT,
            vzd.GameVariable.HITS_TAKEN,
            vzd.GameVariable.DAMAGECOUNT,
            vzd.GameVariable.DAMAGE_TAKEN,
            vzd.GameVariable.POSITION_X,
            vzd.GameVariable.POSITION_Y
            ]

        self.vars_dict = {'KILLCOUNT':0, 'DEATHCOUNT':0,
                          'HITCOUNT':0, 'HITS_TAKEN':0,
                          'DAMAGECOUNT':0, 'DAMAGE_TAKEN':0,
                          'POSITION_X':0, 'POSITION_Y':0}

        self.vars_dict_last = self.vars_dict.copy() #for tracking deltas

        # load_config could be used to load configuration instead of doing it here with code.

        # Sets path to additional resources wad file which is basically your scenario wad.
        # If not specified default maps will be used and it's pretty much useless... unless you want to play good old Doom.
        self.game.set_doom_scenario_path(os.path.join(vzd.scenarios_path, 
                                                      "basic.wad"))

        if not self.scenario_bool:
            # Sets map to start (scenario .wad files can contain many maps).
            self.game.set_doom_map(self.map)

        elif self.scenario_bool:
            #load the scenario file:
            #https://github.com/Farama-Foundation/ViZDoom/tree/master/scenarios
            scenario = os.path.join(vzd.scenarios_path, self.scenario_path)
            self.game.load_config(scenario)

        #Default is 800x600;320X240;256X192;200X150
        self.game.set_screen_resolution(vzd.ScreenResolution.RES_320X240)

        ## Set Render Conditions
        self.game.set_screen_format(vzd.ScreenFormat.BGR24) #RGB24; cv2 is BGR
        self.game.set_labels_buffer_enabled(True) # Enables labeling of the in game objects.

        # Sets other rendering options (all of these options except crosshair are enabled (set to True) by default)
        self.game.set_render_hud(True)
        self.game.set_render_minimal_hud(False)  # If hud is enabled
        self.game.set_render_crosshair(False)
        self.game.set_render_weapon(True)
        self.game.set_render_decals(True)  # Bullet holes and blood on the walls
        self.game.set_render_particles(True)
        self.game.set_render_effects_sprites(True)  # Smoke and blood
        self.game.set_render_messages(True)  # In-game messages
        self.game.set_render_corpses(True)
        self.game.set_render_screen_flashes(True)  # Effect upon taking damage or picking up items

        """ Automap Stuff
        self.game.set_automap_buffer_enabled(True)
        self.game.set_automap_mode(vzd.AutomapMode.WHOLE) #OBJECTS_WITH_SIZE
        self.game.set_automap_render_textures(False)
        self.game.set_automap_rotate(False)
        # This CVAR can be used to make a map follow a player.
        #self.game.add_game_args("+am_followplayer 1")# This CVAR can be used to make a map follow a player.
        # This CVAR controls scale of rendered map (higher valuer means bigger zoom).
        #self.game.add_game_args("+viz_am_scale 2") #10
        # This CVAR shows the whole map centered (overrides am_followplayer and viz_am_scale).
        self.game.add_game_args("+viz_am_center 1")
        # Map's colors can be changed using CVARs, full list is available here: https://zdoom.org/wiki/CVARs:Automap#am_backcolor
        self.game.add_game_args("+am_backcolor 000000")
        """


        self.game.set_available_buttons(self.action_set)# Adds buttons that will be allowed to use.
        n = self.game.get_available_buttons_size()#all possible permutations, since multiple actions can be executed at once.
        #self.action_set_permutations = [list(a) for a in it.product([0, 1], repeat=n)] #for overlapping moves
        self.action_set_permutations = single_button_permutations(len(self.action_set))
        #print("Available buttons:", [b.name for b in self.game.get_available_buttons()])

        self.game.set_available_game_variables(self.variables_set)
        print("Available game variables:", [v.name for v in self.game.get_available_game_variables()])

        self.game.set_episode_timeout(self.total_frame_limit) # Causes episodes to finish after n tics (actions)
        self.game.set_episode_start_time(10) # Makes episodes start after 10 tics (~after raising the weapon)
        self.game.set_window_visible(self.window_show_bool) # Makes the window appear (turned on by default)

        # Sets ViZDoom mode (PLAYER, ASYNC_PLAYER, SPECTATOR, ASYNC_SPECTATOR, PLAYER mode is default)
        self.game.set_mode(vzd.Mode.PLAYER)
        self.game.set_doom_skill(self.difficulty) #1-5
        #self.game.set_ticrate(1000) #only works for async

        #game.set_console_enabled(True) # Enables engine output to console
        # Initialize the game. Further configuration won't take any effect from now on.
        self.game.init()
        #Allow respawns in single player
        self.game.send_game_command("sv_singleplayerrespawn 1")

    @function_timer
    def game_loop(self):
        """Game Loop"""
        actions = self.action_set_permutations
        episodes = 100 # Run this many episodes

        sleep_time = 0 #1.0 / vzd.DEFAULT_TICRATE  # = 0.028
        frame_count = 0

        for i in range(episodes):
            print("Episode #" + str(i + 1))
            # Starts a new episode. It is not needed right after init() but it doesn't cost much. At least the loop is nicer.
            self.game.new_episode()
            #MAP07
            if self.map == "MAP07": #Manual setup for mission.
                self.game.make_action(actions[8]) # open door

            #self.game.send_game_command("sv_singleplayerrespawn 1")
            state = self.game.get_state()
            while not self.game.is_episode_finished():

                # Gets the state
                state_ = self.game.get_state()

                # Which consists of:
                n = state_.number
                vars_set = state_.game_variables #the variables we are tracking.
                screen_buf = state_.screen_buffer #screenshot

                # Shows automap buffer
                map = state_.automap_buffer
                if map is not None:
                    print("showing map:")
                    cv2.imshow('ViZDoom Automap Buffer', map)
                    cv2.waitKey(1)
                #cv2.imshow('ViZDoom Screen Buffer', screen_buf)
                #cv2.waitKey(1)

                # Games variables can be also accessed via
                # (including the ones that were not added as available to a game state):
                #game.get_game_variable(GameVariable.AMMO2)

                # Makes an action (here random one) and returns a reward.
                rand_action = choice(actions)
                for _ in range(10):
                        self.game.make_action(rand_action)
                r, t = self.reward_rules(vars_set, n, False, [])

                print(frame_count)
                frame_count +=1
                if sleep_time > 0:
                        sleep(sleep_time)

            # Check how the episode went.
            print(f"Episode finished; Total Frames: {frame_count}")
            #print("Total reward:", self.game.get_total_reward())
            print("************************")

        self.game.close()

    def reward_rules(self, action, vars_list, frame_count, death_bool, labels):
        """Reward Function is calculated here as all the neccessary variables are
        calculated locally. Different values are contained in self.r_rules"""

        #First convert vars_list to a labeled dict w/ rounded xy coords.
        dict_labels = ['KILLCOUNT', 'DEATHCOUNT', 'HITCOUNT',
                       'HITS_TAKEN', 'DAMAGECOUNT', 'DAMAGE_TAKEN',
                       'POSITION_X', 'POSITION_Y']
        for i, var in enumerate(vars_list):
            if i in (6, 7):
                self.vars_dict[dict_labels[i]] = round(var)
            else:
                self.vars_dict[dict_labels[i]] = var

        terminal = False
        reward = self.r_rules['passive'] #cost of existing/no enemy on screen

        ## See if we're in a spillover state.
        if self.w_varz['hit_spillover'] > 0:
            reward = self.r_rules['spillover']
            self.w_varz['hit_spillover'] -= 1

        ## Check for enemies on screen
        ## No attacking if there are no enemies
        enemy_bool = False
        screen_bonus = 0
        for label in labels:
            #print(label.object_name)
            if str(label.object_name) in self.w_varz['enemy_names']:
                screen_bonus += self.r_rules['enemy_screen']
                enemy_bool = True
                #break
        reward += screen_bonus
        if action == 5 and not enemy_bool:
            #attacked without enemy on screen
            reward += self.r_rules['dry_fire']

        ## Check for Kill
        if self.vars_dict['KILLCOUNT'] > self.vars_dict_last['KILLCOUNT']:
            self.scored_kill = True
            print(f"KILL!: {self.vars_dict['KILLCOUNT']}")
            reward += self.r_rules['scored_kill']

        ## Check if we died
        if death_bool: #we died
            print("Reset: DIED")
            reward = self.r_rules['died']
            terminal = True

        ## Delt a hit(Magnitude)
        v1 = self.vars_dict['DAMAGECOUNT']
        v2 = self.vars_dict_last['DAMAGECOUNT']
        if v1 > v2:
            #Reward is scaled to magnitude set by max(dmg_out_que)
            dmg_out_delta = v1 - v2
            self.w_varz['dmg_out_que'].append(dmg_out_delta)

            #like c map function:(input val, [in_min,in_max],[out_min,out_max])
            r_dice = np.interp(dmg_out_delta, 
                               [min(self.w_varz['dmg_out_que']),
                                max(self.w_varz['dmg_out_que'])],
                               [self.r_rules['dmg_out_min'],
                                self.r_rules['dmg_out_max']])
            reward += r_dice
            self.w_varz['hit_spillover'] = self.hit_bonus
            #print(f"HIT DELT!: {dmg_out_delta} yielded +{round(reward, 2)}")

        ## Felt a hit(Magnitude)
        v1 = self.vars_dict['DAMAGE_TAKEN']
        v2 = self.vars_dict_last['DAMAGE_TAKEN']
        if v1 > v2:
            #Reward is scaled to magnitude set by max(dmg_in_que)
            dmg_in_delta = v1 - v2
            self.w_varz['dmg_in_que'].append(dmg_in_delta)
            #like c map function:(input val, [in_min,in_max],[out_min,out_max])
            r_dice = np.interp(dmg_in_delta,
                               [min(self.w_varz['dmg_in_que']),
                                max(self.w_varz['dmg_in_que'])],
                               [self.r_rules['dmg_in_min'],
                                self.r_rules['dmg_in_max']])
            reward -= r_dice
            #print(f"*HIT FELT!: {dmg_in_delta} yielded -{round(r_dice, 2)}")

        if frame_count >= self.total_frame_limit-1:
            print("Reset: Timed Out")
            terminal = True

        ## check to see if we're moving.
        b1 = (self.vars_dict['POSITION_X']==self.vars_dict_last['POSITION_X'])
        b2 = (self.vars_dict['POSITION_Y']==self.vars_dict_last['POSITION_Y'])
        if (b1 and b2):
            self.w_varz['stuck_counter'] += 1
            if self.w_varz['stuck_counter'] >= 40:
                reward += self.r_rules['stuck']
            if self.w_varz['stuck_counter'] >= 300:
                print(f"STUCK OUT: {self.w_varz['stuck_counter']}")
                reward = self.r_rules['stuck_timeout']
                terminal = True

        self.vars_dict_last = self.vars_dict.copy()

        self.w_varz['reward_que'].append(reward)
        avg_reward = round(np.mean(self.w_varz['reward_que']),2)

        return avg_reward, terminal

    def resize(self, img, wrong_way_bool=False):
        img = np.array(img)
        img = cv2.resize(img, (self.xy, self.xy))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #we're already BG
        #equalize the image for greater contrast.
        img = cv2.equalizeHist(img)

        """#pre process.
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img = std * img + mean
        img = np.clip(img, 0, 1)
        """
        #pre process.
        mean1 = np.mean([0.485, 0.456, 0.406])
        mean = np.array([mean1])
        std1 = np.mean([0.229, 0.224, 0.225])
        std = np.array([std1])
        img = std * img + mean
        img = np.clip(img, 0, 1)

        #cv2.imshow('ViZDoom Screen Buffer', img)
        #cv2.waitKey(1)
        img = np.reshape(img, (self.xy, self.xy, 1))

        return img

    def wrapper_reset(self):
        self.w_varz['stuck_counter'] = 0
        self.scored_kill = False #reset the variable
        self.w_varz['reward_que'] = deque(maxlen=10)

if __name__ == "__main__":

    doom_instance = DoomGame(total_frame_limit=2000)
    doom_instance.game_loop()
