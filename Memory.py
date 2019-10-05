
import sc2
from sc2.unit import Unit
from sc2.position import Point2

from sc2.constants import UnitTypeId

import numpy as np

from dicts.canCloak import CAN_CLOAK


#TODO: consider blips
#TODO: consider snapshots
#TODO: consider so many other things!
#TODO: integrate the attribute system

class UnitMemory:
    def __init__(self, unit : Unit):

        self.unit = unit
        self.tag = unit.tag
        self.type_id = unit.type_id
        self.position : Point2 = unit.position

        self.speed2 = 0
        self.health = unit.health
        self.shield = unit.shield
        self.lost_hp = 0
        self.lost_shield = 0
        self.ignore_count = 0
        self.group_id = None
        self.last_attack_target = None
        self.is_enemy = unit.is_enemy
        if unit.is_enemy:
            self.missing = 0 #How many ticks unit was not-seen
            self.facing = unit.facing #last known facing direction
            self.energy = unit.energy #last energy known
            self.energy_max = unit.energy_max
            self.delta_position: Point2 = Point2((0, 0)) #delta_position is used to propagate position when enemy is hidden/cloaked
            self.is_cloaked = unit.is_cloaked


    def update(self, unit : Unit):
        assert unit.tag == self.tag

        self.unit = unit
        self.speed2 = self.position.distance_to_point2(unit.position)
        #TODO: improve lost hp/shield to be over more than just 1 tick!
        self.lost_hp = self.health - unit.health
        self.lost_shield = self.shield - unit.shield
        self.health = unit.health
        self.shield = unit.shield
        if unit.is_enemy:
            self.facing = unit.facing
            self.energy = unit.energy
            self.delta_position = Point2((0, 0)) if self.missing else unit.position - self.position
            self.is_cloaked = unit.is_cloaked
            self.missing = 0
            self.energy = min(self.energy_max, self.energy + 0.7875/11) #TODO: make this a constant defined
        self.position = unit.position

    #update a enemy unit that is no longer visible
    def update_memory(self):
        assert self.is_enemy
        self.missing += 1 #update time since seen
        self.position += self.delta_position #propogate position
        self.delta_position *= 0.9



# Can serve as memory for friendly or enemy units
class Memory:
    def __init__(self):
        self.units = {}

    def start_tick(self):
        for u in self.units.values():
            u.unit = None


    #Return the memory of this enemy (which might be new)
    def see_unit(self, unit : Unit):

        memory = self.units.get(unit.tag, None)
        if not memory:
            memory = UnitMemory(unit)
            self.units[unit.tag] = memory

        memory.update(unit)
        return memory


    def process_missing_friendly_units(self):
        # remove all items that no longer exist really
        remove_keys = []
        for key,unit in self.units.items():
            if not unit.unit:
                remove_keys.append(key)
        for key in remove_keys:
            del self.units[key]


    def process_missing_enemy_units(self, agent : sc2.BotAI):
        # Here they only get removes if missing or outdated
        # Otherwise they get updated without a unit
        remove_keys = []
        for key,unit in self.units.items():
            if not unit.unit:
                if unit.missing >= 11*5 or unit.health < 5:
                    remove_keys.append(key)
                else:
                    unit.update_memory()
                    if agent.is_visible(unit.position):
                        #TODO: improve cloak mechanics
                        if unit.is_cloaked or unit.type_id in CAN_CLOAK:
                            unit.is_cloaked = True
                        else:
                            unit.missing += 6 # ??

        for key in remove_keys:
            del self.units[key]

