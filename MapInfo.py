import numpy as np

import os

from sc2 import BotAI



import Flood



# A system that stores data for specific maps but caches them so that in real games on ladder it loads fast from npy files!
class MapInfo:

    def __init__(self, map_name, agent : BotAI):
        self.map_name = map_name

        filename1 = f"mapinfo/map_{map_name}_d.npy"
        if os.path.exists(filename1):
            self.dist_from_wall : np.ndarray = np.load(filename1, allow_pickle=True)
            assert self.dist_from_wall.shape == agent.game_info.pathing_grid.data_numpy.shape
        else:
            self.dist_from_wall : np.ndarray = Flood.calculate_distance_from_unpathable(agent.game_info.pathing_grid)
            assert self.dist_from_wall.dtype == np.int32
            np.save(filename1, self.dist_from_wall)


