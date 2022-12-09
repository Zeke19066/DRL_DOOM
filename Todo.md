
# Heading level 1

I just love **bold text**.

Italicized text is the *cat's meow*.


Paradigm shift: All relevant variables are
constantly being added to an SQL database, and
are analyzed independently by the GUI whent they
are pulled. 


NN Machine Vision Doom Agent

How do you beat a doom level?
    1) Explore the environment for the exit.
    1) Avoid Incoming Damage,
    2) Eliminate enemeies when neccessary


Reward Function:

    Incentivise power wapons by boosting the passive Reward when a shotgun is in hand.

    ***Scoring damage is more important than avoiding damage. This turns out to be false, only because the enemies deal so much damage death can happen quickly. Maybe enableing god mode is the right move?

    Spillover of reward over a few cycles helps correlate the statespace.

Behavior Problems:
    The agent becomes trigger happy, and wastes bullets by firing almost continously.
    Solution: If a gun is fired when there are no enemies on screen, penalty.
    Also, add the on screen enemies bonus to the scenario.

Training Parameters:
    Run multiple sessions at once, only learn from
    those that score above avg DPS Out, below avg DPS In,
    and if multiple qualify, then take the one with the longer
    life span.

-----------------------------------------------------------------
Button
Enum type that defines all buttons that can be "pressed" by the agent.

Binary buttons
Binary buttons have only 2 states "not pressed" if value 0 and "pressed" if value other then 0.

ATTACK
USE
JUMP
CROUCH
TURN180
ALTATTACK
RELOAD
ZOOM
SPEED
STRAFE
MOVE_RIGHT
MOVE_LEFT
MOVE_BACKWARD
MOVE_FORWARD
TURN_RIGHT
TURN_LEFT
LOOK_UP
LOOK_DOWN
MOVE_UP
MOVE_DOWN
LAND
SELECT_WEAPON1
SELECT_WEAPON2
SELECT_WEAPON3
SELECT_WEAPON4
SELECT_WEAPON5
SELECT_WEAPON6
SELECT_WEAPON7
SELECT_WEAPON8
SELECT_WEAPON9
SELECT_WEAPON0
SELECT_NEXT_WEAPON
SELECT_PREV_WEAPON
DROP_SELECTED_WEAPON
ACTIVATE_SELECTED_ITEM
SELECT_NEXT_ITEM
SELECT_PREV_ITEM
DROP_SELECTED_ITEM
Delta buttons
Buttons whose value defines the speed of movement. A positive value indicates movement in the first specified direction and a negative value in the second direction. For example: value 10 for MOVE_LEFT_RIGHT_DELTA means slow movement to the right and -100 means fast movement to the left.

LOOK_UP_DOWN_DELTA
TURN_LEFT_RIGHT_DELTA
MOVE_FORWARD_BACKWARD_DELTA
MOVE_LEFT_RIGHT_DELTA
MOVE_UP_DOWN_DELTA

ScreenResolution
Enum type that defines all supported resolutions - shapes of screenBuffer, depthBuffer, labelsBuffer and automapBuffer in State.

RES_160X120 (4:3)
RES_200X125 (16:10)
RES_200X150 (4:3)
RES_256X144 (16:9)
RES_256X160 (16:10)
RES_256X192 (4:3)
RES_320X180 (16:9)
RES_320X200 (16:10)
RES_320X240 (4:3)
RES_320X256 (5:4)
RES_400X225 (16:9)
RES_400X250 (16:10)
RES_400X300 (4:3)
RES_512X288 (16:9)
RES_512X320 (16:10)
RES_512X384 (4:3)
RES_640X360 (16:9)
RES_640X400 (16:10)
RES_640X480 (4:3)
RES_800X450 (16:9)
RES_800X500 (16:10)
RES_800X600 (4:3)
RES_1024X576 (16:9)
RES_1024X640 (16:10)
RES_1024X768 (4:3)
RES_1280X720 (16:9)
RES_1280X800 (16:10)
RES_1280X960 (4:3)
RES_1280X1024 (5:4)
RES_1400X787 (16:9)
RES_1400X875 (16:10)
RES_1400X1050 (4:3)
RES_1600X900 (16:9)
RES_1600X1000 (16:10)
RES_1600X1200 (4:3)
RES_1920X1080 (16:9)

GameVariable
Enum type that defines all variables that can be obtained from the game.

Defined variables
KILLCOUNT - Counts the number of monsters killed during the current episode. Killing other players/bots do not count towards this. From 1.1.5 killing other players/bots counts towards this.
ITEMCOUNT - Counts the number of picked up items during the current episode.
SECRETCOUNT - Counts the number of secret location/objects discovered during the current episode.
FRAGCOUNT - Counts the number of players/bots killed, minus the number of committed suicides. Useful only in multiplayer mode.
DEATHCOUNT - Counts the number of players deaths during the current episode. Useful only in multiplayer mode.
HITCOUNT - Counts number of hit monsters/players/bots during the current episode. Added in 1.1.5.
HITS_TAKEN - Counts number of hits taken by the player during the current episode. Added in 1.1.5.
DAMAGECOUNT - Counts number of damage dealt to monsters/players/bots during the current episode. Added in 1.1.5.
DAMAGE_TAKEN - Counts number of damage taken by the player during the current episode. Added in 1.1.5.
HEALTH - Can be higher then 100!
ARMOR - Can be higher then 100!
DEAD - True if the player is dead.
ON_GROUND - True if the player is on the ground (not in the air).
ATTACK_READY - True if the attack can be performed.
ALTATTACK_READY - True if the altattack can be performed.
SELECTED_WEAPON - Selected weapon's number.
SELECTED_WEAPON_AMMO - Ammo for selected weapon.
AMMO0 - AMMO9 - Number of ammo for weapon in N slot.
WEAPON0 - WEAPON9 - Number of weapons in N slot.
POSITION_X - Position of the player, not available if viz_nocheat is enabled.
POSITION_Y
POSITION_Z
ANGLE - Orientation of the player, not available if viz_nocheat is enabled.
PITCH
ROLL
VIEW_HEIGHT - View high of the player, not available if viz_nocheat is enabled. Position of the camera in Z axis is equal to POSITION_Z + VIEW_HEIGHT. Added in 1.1.7.
VELOCITY_X - Velocity of the player, not available if viz_nocheat is enabled.
VELOCITY_Y
VELOCITY_Z
CAMERA_POSITION_X - Position of the camera, not available if viz_nocheat is enabled. Added in 1.1.7.
CAMERA_POSITION_Y
CAMERA_POSITION_Z
CAMERA_ANGLE - Orientation of the camera, not available if viz_nocheat is enabled. Added in 1.1.7.
CAMERA_PITCH
CAMERA_ROLL
CAMERA_FOV - Field of view in degrees, not available if viz_nocheat is enabled. Added in 1.1.7.
PLAYER_NUMBER - Player's number in multiplayer game.
PLAYER_COUNT - Number of players in multiplayer game.
PLAYER1_FRAGCOUNT - PLAYER16_FRAGCOUNT - Number of N player's frags