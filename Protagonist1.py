

import sc2
from TrainableAgent import TrainableAgent
from AgentBrain import AgentBrain

from sc2.position import Point2
from sc2.unit import Unit
from sc2.constants import UnitTypeId

import Flood
import pickle

from BaseAgentA1 import BaseAgentA1


class Protagonist(BaseAgentA1, TrainableAgent):
    def __init__(self, master, *args):
        BaseAgentA1.__init__(self, *args)
        TrainableAgent.__init__(self)
        self.master  = master
        self.brain = AgentBrain()

        # disable macro and set training mode tactics for now
        self.disable_macro = True
        self.enemy_location_0 : Point2 = None
        self.enemy_location_1: Point2 = None

        self.do_it = False
        self.do_it2 = False

    async def on_start(self):
        self.master.register_player(self)
        self.enemy_location_0 = self.game_info.map_center
        await super(Protagonist,self).on_start()

        # if self.player_id == 1:
        #     distance_from = Flood.calculate_distance_from_unpathable(self.game_info.pathing_grid)
        #     with open("dist_from1.p","wb") as f:
        #         pickle.dump(distance_from, f)
        #
        #     choke, labels, _ = Flood.calculation_choke_points(self.game_info.pathing_grid, distance_from=False , map=distance_from)
        #     with open("choke_points.p","wb") as f:
        #         pickle.dump(choke, f)
        #     with open("areas1.p", "wb") as f:
        #         pickle.dump(labels, f)


    async def on_building_construction_complete(self, unit: Unit):
        print("New building popped up!!")
        await super(Protagonist, self).on_building_construction_complete(unit)

    async def on_upgrade_complete(self, upgrade):
        #print(f"Got Upgrade: {upgrade}")
        await super(Protagonist, self).on_upgrade_complete(upgrade)

    async def on_unit_destroyed(self, unit_tag):
        await super(Protagonist, self).on_unit_destroyed(unit_tag)


    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.master.step0_setup(self)
            self.do_it = True
            return

        if self.master.setup_in_progress:
            #setup is in progress
            await self.master.setup_scenario(self)
            self.do_it = True
        else:
            #TODO: implement this Protagonist's code

            if self.do_it:
                #First attack towards centre
                self.do_it = False
                self.do_it2 = True
                print(f"{self.player_id} Attacking now!")
                u: Unit
                for u in self.units:
                    self.do(u.attack(self.enemy_location_0))

            elif self.do_it2:
                #Queue attack to enemy position (in-case enemy is slower)
                self.do_it2 = False
                u: Unit
                for u in self.units:
                    self.do(u.attack(self.enemy_location_1, queue=True))

            else:
                #Process units
                pass



            # Check if scenario ended?
            self.master.check_scenario_end(self)


    #protagonist doesn't have a brain at this stage
    def use_brain(self, brain : AgentBrain):
        pass
    def get_brain(self) -> AgentBrain:
        # Fake brain just to make the trained happy
        return self.brain
