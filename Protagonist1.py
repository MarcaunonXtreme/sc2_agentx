

import sc2
from TrainableAgent import TrainableAgent
from AgentBrain import AgentBrain

from sc2.position import Point2
from sc2.unit import Unit
from sc2.constants import UnitTypeId

from Memory import UnitMemory, Memory

import Flood
import pickle

from BaseAgentA1 import BaseAgentA1


class Protagonist(BaseAgentA1, TrainableAgent):
    def __init__(self, master, global_debug, *args):
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

        self.global_debug = global_debug

        self.enemy_memory : Memory = None 

    async def on_start(self):
        self.master.register_player(self)
        self.enemy_location_0 = self.game_info.map_center
        await super(Protagonist,self).on_start()

        #await self.client.debug_show_map()

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
                if iteration % 8 == 0:
                    await self.process_units()
                




            # Check if scenario ended?
            await self.master.check_scenario_end(self)


    async def process_units(self):

        #if not self.enemy_units:
        #    return

        u : Unit 
        for u in self.units:

            #if u.type_id == UnitTypeId.RAVAGER:
            #    await self.process_ravager(u)

            #Fallback, attack towards closest enemy for now
            #This is just a simple method, can improve a lot obviously
            #Attack towards closest enemy unit.
            
            #TODO: if defending this need to be completely different?
            e = self.game_info.map_center
            if self.enemy_memory is not None:

                best_dist = 1000.0
                for mem in self.enemy_memory.values: #type: UnitMemory
                    dist = mem.position.distance_to(u)
                    if dist < best_dist:
                        best_dist = dist
                        e = mem.position

            else:
                print("WARNING: don't have enemy memory")
                if self.enemy_units:
                    e = self.enemy_units.closest_to(u)
            if e:
                self.do(u.attack(e.position))





    async def process_ravager(self, u : Unit):
        #TODO: if on cd use corrosive bile on random target
        pass

    async def process_queen(self, u : Unit):
        #TODO: if enough energy use heal ability on a friendly in need
        pass

    async def process_MM(self, u:Unit):
        #TODO: if enemies in range and hp > threshold -> activate stimpack
        pass
    
    async def process_reaper(self, u:Unit):
        #TODO: KD8 charge a target?
        pass

    async def process_tank(self, u:Unit):
        #TODO: switch modes
        pass 

    async def process_stalker(self,u :Unit):
        #TODO: if enemies in range and shields down blink away from closest unit.
        #TODO: if enemies very close also blink away maybe?
        pass

    async def process_sentry(self, u : Unit):
        #TODO: if enemy units on main base ramp - FF it.
        #TODO: if range enemy units nearby use guardian shield maybe
        #TODO: use force fields to scatter enemy units
        pass

    async def process_adept(self, u:Unit):
        #TODO: use psionic transfer somehow?
        pass
    
    async def process_highTemplar(self, u: Unit):
        #TODO: use feedback on enemy units randomly with above threshold energy
        #TODO: randomly use storm if over 150 energy. (randomly target enemy units?)
        pass

    async def process_disruptor(self, u :Unit):
        #TODO: use purification nova and try to approach enemy units with it.
        pass

    #protagonist doesn't have a brain at this stage
    def use_brain(self, brain : AgentBrain):
        pass
    def get_brain(self) -> AgentBrain:
        # Fake brain just to make the trained happy
        return self.brain
