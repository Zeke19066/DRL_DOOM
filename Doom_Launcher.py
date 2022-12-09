import Doom_Train_A2C as Doom_Train

import multiprocessing
import os
import time

#Note: Ensure DXWnd wrapper is open and calibrated correctly before launching.

#Modes = "Train", "Test"
mode = "Train"

def main(mode):
    print(f"Pre-Startup Mode:{mode};")

    if mode == "Train":
        import Doom_GUI
        mode = 'train'

        #Initialize multiprocess pipeline.
        send_connection, recieve_connection = multiprocessing.Pipe()
        gui_process = multiprocessing.Process(target=Doom_GUI.main, 
                                            args=(recieve_connection,)) #gotta leave that comma
        nn_process = multiprocessing.Process(target=Doom_Train.main, 
                                            args=(mode, send_connection))

        nn_process.start()
        gui_process.start()

        while 1:
            time.sleep(1)

if __name__ == "__main__":
    main(mode)