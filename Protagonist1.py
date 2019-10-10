

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
        super(Protagonist,self).__init__(*args)
        self.master  = master
        self.brain = AgentBrain()



        # disable macro and set training mode tactics for now
        self.disable_macro = True
        self.enemy_location_0 : Point2 = None



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
        self.master.new_building(self,unit)
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

        return
        if self.master.setup_in_progress:
            #setup is in progress
            await self.master.setup_scenario(self)
            self.do_it = True
        else:
            if self.do_it:
                self.do_it = False
                u : Unit
                for u in self.units:
                    self.do(u.attack(self.enemy_location_0))

            death_struct = self.structures.find_by_tag(self.death_struct_tag)
            if death_struct and not self.protect:
                if death_struct.health < death_struct.health_max:
                    self.protect = True
                    for u in self.units:
                        self.do(u.attack(death_struct.position))


            # Check if scenario ended?
            self.master.check_scenario_end(self)


    #protagonist doesn't have a brain at this stage
    def use_brain(self, brain : AgentBrain):
        pass
    def get_brain(self) -> AgentBrain:
        # Fake brain just to make the trained happy
        return self.brain
