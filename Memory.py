
import sc2
from sc2.unit import Unit
from sc2.position import Point2

from sc2.constants import UnitTypeId

import numpy as np

from luts.canCloak import CAN_CLOAK

from sc2.dicts.unit_unit_alias import UNIT_UNIT_ALIAS

from sc2.constants import IS_LIGHT, IS_ARMORED, IS_BIOLOGICAL, IS_MECHANICAL, IS_MASSIVE

from luts.attackUpgrades import *

#TODO:
from UnitInfo import get_unit_info, UnitInfoBase

#TODO: consider blips
#TODO: consider snapshots
#TODO: consider so many other things!
#TODO: integrate the attribute system

class UnitMemory:
    def __init__(self, unit : Unit, info : UnitInfoBase):
        assert isinstance(info, UnitInfoBase)

        self.info = info
        self.unit = unit
        self.tag = unit.tag
        self.type_id = info.type_id
        self.current_type_id = 0
        self.position : Point2 = unit.position

        #melee or ranged?
        self.is_melee = max(unit.air_range, unit.ground_range) > 2.0
        #flying or ground unit?
        self.is_flying = unit.is_flying #Note: Deal with vikings exception!
        # light/armored/none?
        self.is_light = unit.is_light
        self.is_armored = unit.is_armored
        # biological/mechanical/none?
        self.is_biological = unit.is_biological
        self.is_mechanical = unit.is_mechanical
        #special:
        self.is_massive = unit.is_massive

        self.radius = unit.radius
        self.speed2 = 0
        self.health = unit.health
        self.shield = unit.shield
        self.lost_hp = 0
        self.lost_shield = 0
        self.armor = 0
        self.shield_armor = 0

        self.movement_speed = self.info.get_movement_speed()

        weapon_ground = next((weapon for weapon in unit._weapons if weapon.type in TARGET_GROUND), None)
        weapon_air = next((weapon for weapon in unit._weapons if weapon.type in TARGET_AIR), None)
        #TODO: use a namedtuple rather:
        if weapon_ground:
            self.ground_damage = (weapon_ground.damage , weapon_ground.attacks, weapon_ground.speed)
        else:
            self.ground_damage = (0, 0, 1)

        if weapon_air:
            self.air_damage = (weapon_air.damage, weapon_air.attacks, weapon_air.speed)
        else:
            self.air_damage = (0, 0, 1)

        self.attack_upgrade_factor = ATTACK_UPGRADE_INC.get(self.type_id, ATTACK_UPGRADE_DEFAULT)
        self.bonus_dmg = ATTACK_BONUS_DAMAGE.get(self.type_id, None)
        self.weapon_upgrade = 0

        self.ignore_count = 0
        self.group_id = None

        self.glass_cannon_ratio = max(unit.ground_dps, unit.air_dps) / ((unit.health_max + unit.shield_max)*(1.0 + 0.1*unit.armor))

        self.is_enemy = unit.is_enemy
        if unit.is_enemy:
            self.missing = 0 #How many ticks unit was not-seen
            self.facing = unit.facing #last known facing direction
            self.energy = unit.energy #last energy known
            self.energy_max = unit.energy_max
            self.delta_position: Point2 = Point2((0, 0)) #delta_position is used to propagate position when enemy is hidden/cloaked
            self.is_cloaked = unit.is_cloaked


        ##the following is used by the macro system:
        if unit.is_enemy:
            #for enemies:
            self.attacking_previous_melee = 0
            self.attacking_previous_range = 0
            self.attack_count_melee = 0
            self.attack_count_range = 0

            self.closest_friendly_dist = 10.0
            self.closest_friendly_tag = 0

            
        else:
            #for friendlies:
            self.enemy_in_range_count = 0
            self.friend_in_range_count = 0
            self.last_attack_target = None

            self.radar = np.zeros((8,42)) # used by radar for movement decisions

            self.friendly_centre : Point2 = None # Centre of gravity of friendly units
            self.enemy_centre : Point2 = None # Centre of gravity of enemy units

            self.closest_enemy_dist = 10.0

            self.delta_power_projection = 0.0
            self.delta_power_projection_lpf = 0.0
            self.good_bad = 0
            self.attack_mode = False

        #both:
        self.surround_length = 0.0
        self.can_attack_count = 0
        #self.delta_power_projection = 0.0 #this is the micro short range one
        #self.delta_power_projection2 = 0.0  #this one is used for long distance decision making TODO
        self.power_projection = 0.0

        #unit.attacking_count_melee = 0
        # unit.attacking_count_range = 0
        # unit.can_attack_count = 0
        # unit.attack_power = 0.0

        #Used by micro agent to cache network to use:
        self.move_network = None
        self.attack_network = None
        self.special_network = None


    def got_attribute(self, attr):
        if attr is IS_LIGHT:
            return self.is_light
        elif attr is IS_ARMORED:
            return self.is_armored
        elif attr is IS_BIOLOGICAL:
            return self.is_biological
        elif attr is IS_MECHANICAL:
            return self.is_mechanical
        elif attr is IS_MASSIVE:
            return self.is_massive
        else:
            return False

    #This function returns (damage_vs_hp , damage_vs_shield, dps, time_to_kill)
    # damage_vs_hp is the number of hitpoint damage it will do versus enemy (if no shield left)
    # damage_vs_shield is number of shield points damage it will do versus enemy (assuming it's a protoss unit with shield left)
    # dps - average damage per second versus health/armour (doesn't consider shields)
    # time_to_kill - an estimation of exactly how long it will take to kill the target (assuming it is in range etc.)
    def get_dmg_versus(self, enemy ) :
        #calculate damage output:
        damage = self.air_damage if enemy.is_flying else self.ground_damage # (damage,attacks,speed)
        if damage[0] <= 0:
            return 0 # can't attack this enemy at all
        factor = self.attack_upgrade_factor[1] if enemy.is_flying else self.attack_upgrade_factor[0]

        # calcualte raw non-bonus damage:
        raw_dmg = damage[0] + factor*self.weapon_upgrade
        
        if self.bonus_dmg: #add bonus damage if applicable
            if enemy.got_attribute(self.bonus_dmg[0]):
                raw_dmg += self.bonus_dmg[1] + self.bonus_dmg[2]*self.weapon_upgrade

        #Reduce by armor:
        #TODO: figure out how to consider shield vs armour here?
        hp_dmg = (raw_dmg - enemy.armor) * damage[1] # TODO: upgrades! (like plating on ultra)
        shield_dmg = (raw_dmg - enemy.shield_armor) * damage[1]
        
        # Calculate damage per second: (doesn't consider shields here)
        dps = hp_dmg / damage[2]  #TODO: upgrades

        # Calculate how long it will take to kill the target:
        #Note: this is not perfect yet in the shield/hp edge?
        hits = (enemy.shield+shield_dmg-1) // shield_dmg  + (enemy.health+hp_dmg-1 - (enemy.shield%shield_dmg)) // hp_dmg
        kill_time = hits * damage[2] #TODO: upgrades

        return hp_dmg, shield_dmg, dps, kill_time 



    def update(self, unit : Unit):
        assert unit.tag == self.tag

        self.current_type_id = unit.type_id

        self.unit = unit
        self.speed2 = self.position.distance_to_point2(unit.position)
        #TODO: improve lost hp/shield to be over more than just 1 tick!
        self.lost_hp = self.health - unit.health
        self.lost_shield = self.shield - unit.shield
        self.health = unit.health
        self.shield = unit.shield
        self.armor = unit.armor + unit.armor_upgrade_level #TODO: other upgrades!
        self.shield_armor = unit.shield_upgrade_level
        self.weapon_upgrade = unit.attack_upgrade_level
        if unit.is_enemy:
            self.facing = unit.facing
            self.energy = unit.energy
            self.delta_position = Point2((0, 0)) if self.missing else unit.position - self.position
            self.is_cloaked = unit.is_cloaked
            self.missing = 0
            self.energy = min(self.energy_max, self.energy + 0.7875/11) #TODO: make this a constant defined
            #TODO: track temporary unit life-time to predict when they will go away
        self.position = unit.position

        self.movement_speed = self.info.get_movement_speed()


    #update a enemy unit that is no longer visible
    def update_memory(self):
        assert self.is_enemy
        self.missing += 1 #update time since seen
        self.position += self.delta_position #propogate position
        self.delta_position *= 0.9



# Can serve as memory for friendly or enemy units
class Memory:
    def __init__(self, agent, upgrades):
        assert agent is not None
        assert upgrades is not None
        self.units = {}
        self.upgrades = upgrades
        self.agent = agent
        self.info = {}


    @property
    def values(self):
        return self.units.values()

    def start_tick(self):
        for u in self.units.values():
            u.unit = None


    #Return the memory of this enemy (which might be new)
    def see_unit(self, unit : Unit):

        memory = self.units.get(unit.tag, None)
        if not memory:
            ti = UNIT_UNIT_ALIAS.get(unit.type_id, unit.type_id)
            i = self.info.get(ti, None)
            if not i:
                i = get_unit_info(ti)(self.agent, ti, self.upgrades)
                self.info[ti] = i

            memory = UnitMemory(unit, i)
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

