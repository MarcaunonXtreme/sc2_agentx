
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit

import numpy as np

from sc2.constants import UnitTypeId

import random

from collections import deque

from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.game_data import Cost
from sc2.units import Units

import pickle

from BaseAgentA1 import BaseAgentA1


class MacroAgentB1(BaseAgentA1):

    def __init__(self, starting_bo = []):
        super(MacroAgentB1, self).__init__()
        assert isinstance(starting_bo, list)
        self.bo = starting_bo
        self.bo_index = 0
        self.bo_active = False
        self.unit_priority = []
        self.auto_supply = False
        self.enable_gas_harvest = True

        self.disable_macro = False

        #TODO: gas "target" system
        #TODO: mineral sink system?


    async def on_step(self, iteration: int):
        await super(MacroAgentB1, self).on_step(iteration)

        if self.disable_macro:
            return

        #TODO: Fix this for flat maps with no ramp
        if iteration == 1 and self.race == Race.Zerg and self.game_info.map_ramps:
            th : Unit = self.townhalls[0]
            r : Point2 = self.main_base_ramp.top_center
            rally = Point2.center([th.position, r])
            self.do(th(AbilityId.RALLY_UNITS, rally))

        #TODO: at which time to we set rally for production buildings?

        #TODO: replace any lost buildings?

        #Process current BO
        if self.bo_index < len(self.bo):
            order = self.bo[self.bo_index]

            if self.bo_active:
                #process it:
                r = await order.execute(self)
                if r:
                    #print(f"B Order {self.bo_index} completed")
                    self.bo_index += 1
                    self.bo_active = False
            else:
                self.bo_active = order.can_start(self)
                if self.bo_active:
                    print(f"Starting order = {self.bo_index} : {type(order)}")

        if iteration % 120 == 0:
            #this helps with debugging if something gets stuck
            print(f" Current BO = {self.bo_index} active={self.bo_active}")

        if self.auto_supply:
            await self.make_supply()

        self.balance_workers(iteration)

        self.train_units()

        if self.is_zerg and iteration % 5 == 0:
            self.queen_injects()

        #TODO: minerals sinks


        #TODO: race specific macro


        #TODO: T: supply depot control

    async def make_supply(self):
        # TODO: create supply as necessary!
        if self.supply_cap >= 200:
            return
        supply_avail = self.supply_cap + self.supply_in_production()
        margin = supply_avail - self.supply_used

        #TODO: improve these algorithms.
        if self.race == Race.Zerg:
            nr_hatch = len(self.townhalls)
            nr_queens = len(self.units.filter(lambda u : u.type_id == UnitTypeId.QUEEN))
            nr_queens = min(nr_queens, nr_hatch, 4)
            prod = nr_hatch*2 + nr_queens*2
            if self.structures.filter(lambda ss: ss.type_id == UnitTypeId.LAIR or ss.type_id == UnitTypeId.ROACHWARREN):
                prod *= 2
        elif self.race == Race.Terran:
            prod = 0
            for s in self.structures:
                if s.type_id in [UnitTypeId.COMMANDCENTER,UnitTypeId.ORBITALCOMMAND,UnitTypeId.PLANETARYFORTRESS]:
                    if len(self.workers) < 70:
                        prod += 1
                elif s.type_id == UnitTypeId.BARRACKS:
                    prod += 1
                    if s.has_add_on:
                        prod += 1
                elif s.type_id in [UnitTypeId.FACTORY , UnitTypeId.STARPORT]:
                    prod += 2
                    if s.has_add_on:
                        prod += 1.5 #TODO: actually different for reactor/techlab!
        elif self.race == Race.Protoss:
            raise NotImplementedError
        else:
            raise AssertionError

        required = prod - margin
        if required >= 0:
            print("Building supply (auto)")
            await self.build_one_supply()




    def set_auto_supply(self, enable : bool):
        self.auto_supply = enable

    def set_auto_expand(self, enable : bool):
        pass

    def set_gas_harvesting(self, enable :bool):
        self.enable_gas_harvest = enable

    #TODO: rework this completely! A linear list of priorities isn't good enough!
    def set_unit_priorities(self, unit_priorities : list):
        self.unit_priority = unit_priorities

    def set_tactic_attack(self):
        pass
    def set_tactic_auto(self):
        pass
    def set_tactic_defend(self):
        pass



    def train_units(self):

        #TODO: unit priorities!
        #TODO: limit workers to sensible limits??

        if self.race == Race.Zerg:
            p_index = 0
            drone_shortage = self.worker_shortage
            for larva in self.larva:
                #skip through unit list until something affordable comes up:
                while p_index < len(self.unit_priority) and not self.can_afford(self.unit_priority[p_index]):
                    p_index += 1

                if p_index < len(self.unit_priority):
                    # build unit in priority list:
                    unit_type = self.unit_priority[p_index]
                    if larva.tag not in self.unit_tags_received_action:
                        print(f"Training unit: {unit_type}")
                        self.do(larva.train(unit_type), subtract_cost=True, subtract_supply=True)
                else:
                    #try build drone:
                    if self.minerals < 50 or self.supply_left <= 0 or drone_shortage < -1 or len(self.workers) >= 75:
                        # Can't do anything more
                        #Note: zerg will build up to 2 extra drones for future buildings
                        break
                    if larva.tag not in self.unit_tags_received_action:
                        print("Training another drone")
                        self.do(larva.train(UnitTypeId.DRONE), subtract_cost=True, subtract_supply=True)
                        drone_shortage -= 1

        else:
            #TODO: P/T implementations
            #for unit_type in self.unit_priority:
            for unit_type in self.unit_priority:
                self.train(unit_type,8)

            #Try building workers:
            shortage = self.worker_shortage
            for th in self.townhalls:
                if shortage < 0:
                    break #Build only 1 extra for P/T
                if th.is_idle and self.minerals > 50 and self.supply_left > 0 and len(self.workers) < 75:
                    self.do(th.train(sc2.race_worker[self.race]), subtract_cost=True, subtract_supply=True)
                    shortage -= 1



    #This function attempts to balance workers as possible
    def balance_workers(self, iteration : int):
        if iteration % 3 == 0:
            #Move idle workers
            for w in self.workers:
                if w.is_idle:
                    target : Unit = self.find_closest_minerals(w)
                    if target:
                        self.do(w.gather(target))

        if iteration % 3 == 1:
            self.balance_gas_workers(not self.enable_gas_harvest)

        if iteration % 3 == 2:
            self.balance_mineral_workers()


    #TODO: on_end :)
    #async def on_end(self, game_result: Result):



