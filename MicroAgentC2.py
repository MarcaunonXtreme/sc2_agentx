
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit

import numpy as np
import math

from sc2.constants import UnitTypeId

import random

from collections import deque

from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2, Point3
from sc2.game_data import Cost
from sc2.units import Units

from TrainableAgent import TrainableAgent

from MacroAgentB1 import MacroAgentB1

import AgentBrain

from Memory import Memory, UnitMemory


# ^
# ^
# y
#      3 2 1
#       \|/
#      4-X-0
#       /|\
#      5 6 7
#  x -->

slice_delta = [
    Point2((2,0)),
    Point2((1.4, 1.4)),
    Point2((0,2)),
    Point2((-1.4, 1.4)),
    Point2((-2.0, 0)),
    Point2((-1.4, -1.4)),
    Point2((0, -2.0)),
    Point2((1.4, -1.4))
]

#for the movement algorithm we slice the view up into 8 slices around the unit
#this function calculate the slice number
def determine_slice_nr(unit_position : Point2, target : Point2):
    delta : Point2 = target - unit_position

    #TODO: implement something based on gradient that is faster than atan2 if possible?
    angle = math.atan2(delta.y, delta.x)
    angle = round(angle / (math.pi/4))
    angle += 8
    return angle % 8


# This level of the agent takes care of micro type stuff
class MicroAgentC2(MacroAgentB1, TrainableAgent):

    TACTIC_DEFEND = 1
    TACTIC_ATTACK = 2
    TACTIC_TRAIN_1 = 3 # in this mode it always attacks the enemy "start location" nothing else

    def __init__(self, *args):
        MacroAgentB1.__init__(self, *args)
        TrainableAgent.__init__(self)
        self.tactic = MicroAgentC2.TACTIC_DEFEND
        self.defend_locations = []
        #TODO: deprecate this completely in favour of the memory system!
        self.iteration = -1
        self.delta_step_time = 1.0
        self.brain : AgentBrain.AgentBrain = None
        self.attack_network : AgentBrain.Network = None
        self.move_network : AgentBrain.Network = None

        self.enemy_memory : Memory = Memory()
        self.friendly_memory : Memory = Memory()

    def get_brain(self) -> AgentBrain:
        return self.brain

    def use_brain(self, brain : AgentBrain):
        self.brain = brain
        assert isinstance(self.brain, AgentBrain.AgentBrain)
        #TODO Rather combine this into 1 network!
        #print(f"Agent got a new brain! {self.player_id}")
        self.attack_network = brain.get_network("attack", 42, 2)
        self.move_network = brain.get_network("move", 32, 2, hidden_count=16)
        assert isinstance(self.attack_network, AgentBrain.Network)


    async def on_step(self, iteration: int):
        self.iteration = iteration
        await super(MicroAgentC2,self).on_step(iteration)

        self.delta_step_time = self._client.game_step / 22.0

        #if self.tactic == MicroAgentC1.TACTIC_ATTACK:
        #    time.sleep(150e-3)

        #Make a list of all enemies (units and structures)
        # TODO: filter units into tiles so that the loops only search through local units!?
        self.enemy_memory.start_tick()
        self.friendly_memory.start_tick()

        unit : Unit
        for unit in self.enemy_units.filter(lambda u: u.type_id not in [UnitTypeId.EGG, UnitTypeId.LARVA]):
            mem = self.enemy_memory.see_unit(unit)

            mem.can_attack_count = 0

            mem.attack_count_melee = 0
            mem.attack_count_range = 0
            #unit.attacking_count_melee = 0
            #unit.attacking_count_range = 0
            #unit.can_attack_count = 0
            #unit.attack_power = 0.0
            #enemy_list.append(unit)



        #NOte: if we can modify python-sc2 to insert these in the units list it will make things easier (the static-D)
        for unit in self.enemy_structures.filter(lambda u: (u.can_attack_ground or u.can_attack_air) and u.is_visible):
            mem = self.enemy_memory.see_unit(unit)

            mem.can_attack_count = 0

            mem.attack_count_melee = 0
            mem.attack_count_range = 0

            #unit.attacking_count_melee = 0
            #unit.attacking_count_range = 0
            #unit.can_attack_count = 0
            #unit.attack_power = 0.0

            #enemy_list.append(unit)

        self.enemy_memory.process_missing_enemy_units(self)

        #Find defend locations
        if iteration % 3 == 0:
            self.defend_locations = []
            #TODO: detect locations near our base where enemy units are
            #TODO: this method sucks, should mark the map area based on distance from all bases (and all structures)

        #process units - pre cycle
        ## Precycle determine the following variables for friendly units:
        ### got_enemies : bool - enemies in "era"
        ### enemy_can_attack_count : float - more or less how many enemies can attack us
        ### enemy_attack_power : float - a number indicating the "power projection" the enemy has against this unit
        ## Precycle determine the following variables for enemy units:
        ### can_attack_count : float - more or less how many friendly units can attack this enemy
        ### attack_power : float - a number indicating the "power projection" against this eney
        #_unit_mod = iteration % 3
        #TODO: my own static-D?! (especially for zerg)

        for unit in self.units:
            if unit.type_id not in [UnitTypeId.BROODLING, UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.MULE]:

                mem : UnitMemory = self.friendly_memory.see_unit(unit)

                if not unit.is_active:
                    continue

                mem.enemy_in_range_count = 0
                mem.can_attack_count = 0

                mem.radar.fill(0)
                for i in range(8):
                    mem.radar[i, 0] = 20.0 #for closest friendly unit
                    mem.radar[i, 1] = 20.0 #for closest enemy unit

                enemy : UnitMemory
                for enemy in self.enemy_memory.values:
                    if unit.position._distance_squared(enemy.position) < 100.0: #TODO: make this 15**2
                        mem.enemy_in_range_count += 1

                        #was target previously?
                        if mem.last_attack_target == enemy.tag:
                            if mem.is_melee:
                                enemy.attacking_previous_melee += 1
                            else:
                                enemy.attacking_previous_range += 1

                        #some unit<>enemy calculations
                        dist_to_enemy = unit.distance_to(enemy.position) - unit.radius - enemy.radius



                        #Generate RADAR information
                        s = determine_slice_nr(mem.position, enemy.position)
                        #TODO: also process structures on radar! (as they can block things!)
                        mem.radar[s,1] = min(mem.radar[s,1], dist_to_enemy) #closest enemy unit
                        mem.radar[s,3] += 1 #scale somehow?


                        if enemy.missing == 0:

                            attack_range = unit.air_range if enemy.unit.is_flying else unit.ground_range
                            enemy_attack_range = enemy.unit.air_range if unit.is_flying else enemy.unit.ground_range

                            # Update can_attack_count - useful for managing attack priorities
                            ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy - attack_range) * 5.0 / max(unit.movement_speed,                                                                                                    1.0))
                            enemy.can_attack_count += ratio

                            # see if enemy is facing us?
                            angle = math.atan2(unit.position.y - enemy.position.y, unit.position.x - enemy.position.x) - enemy.facing
                            angle = min(math.fabs(angle), math.fabs(angle - math.pi*2))
                            if angle < 0.020: #Not sure how find to make this
                                if enemy.is_melee:
                                    #TODO: scale this by some kind of threat calculation?
                                    if dist_to_enemy < enemy_attack_range + 0.5:
                                        mem.radar[s,4] += 1
                                else:
                                    if dist_to_enemy < enemy_attack_range + 0.1:
                                        mem.radar[s,5] += 1

                            #we in enemy range in general?
                            if dist_to_enemy < enemy_attack_range + 0.1:
                                mem.radar[s,6] += 1

                            #7 = how far can we move back and still have enemy in range?
                            mem.radar[s,7] = max(mem.radar[s,7], attack_range - dist_to_enemy - 0.1)


        #delete memory of any friendly units that died previously (can maybe do this via a callback??)
        self.friendly_memory.process_missing_friendly_units()


        #
        # for i,unit in enumerate(self.units):
        #     if unit.type_id not in [UnitTypeId.BROODLING, UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.MULE]:
        #         unit.got_enemies = False
        #         unit.enemy_can_attack_count = 0.0
        #         unit.enemy_attack_power = 0.0
        #         unit.enemy_facing_range = 0.0
        #         unit.enemy_facing_melee = 0.0
        #
        #         # TODO: currently need to check ALL enemy units. Using buckets over the map will make this much faster
        #
        #         # TODO: in time need to increase this to 15.0 but for now this is simpler
        #         got_enemies = False
        #         if enemy_list:
        #             enemy : Unit
        #             for enemy in enemy_list.closer_than(10.0, unit):
        #                 got_enemies = True
        #
        #                 #TODO: need to check if CAN actually attack!
        #                 #TODO: should maybe look more than 1 second ahead in distance?
        #                 # Check if we can attack it?
        #                 dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
        #                 attack_range = unit.air_range if enemy.is_flying else unit.ground_range
        #                 attack_dps = unit.air_dps if enemy.is_flying else unit.ground_dps
        #                 enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
        #                 enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps
        #
        #                 ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy-attack_range)*5.0/max(unit.movement_speed,1.0))
        #                 enemy.can_attack_count += ratio
        #
        #                 enemy_ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy-enemy_attack_range)*2.5/max(enemy.movement_speed,1.0))
        #                 unit.enemy_can_attack_count += enemy_ratio
        #
        #                 angle = math.atan2(unit.position.y - enemy.position.y , unit.position.x - enemy.position.x) - enemy.facing
        #                 angle = min(math.fabs(angle), math.fabs(angle - math.pi*2))
        #                 if angle < 0.020: #Not sure how find to make this
        #                     if enemy_attack_range < 2.5:
        #                         unit.enemy_facing_melee += ratio
        #                     else:
        #                         unit.enemy_facing_range += ratio
        #
        #
        #                 #TODO: this still ignores energy levels!
        #                 #TODO: this still ignores armour!
        #                 #TODO: still ignore upgrades!
        #                 #TODO: still ignore creep!
        #                 #TODO: enemies on high ground is more dangerous - also enemies behind chokes like ramps
        #                 #TODO: still ignore special offsets. example a stalker with blink is worth more. baneling splash is worth more etc.
        #                 #TODO: the linear scaling of movement_speed and attack_range separately isn't the best unfortunately!
        #                 #TODO: does not consider upgrades/buffs and all that!
        #                 #
        #                 # power_scale = 1.0
        #                 # power_scale /= max(1.0, 1.0 + (dist_to_enemy-attack_range*1.2-unit.movement_speed*1.2+4.0)*0.5/max(0.5, unit.movement_speed))
        #                 # power_scale *= min(2.5, max(1.0, unit.movement_speed/max(0.1,enemy.movement_speed)))
        #                 # if unit.movement_speed - enemy.movement_speed > 0.1: #Not ideal but not sure how to scale this better currently
        #                 #     power_scale *= min(2.5, max(1.0, attack_range / max(0.1,enemy_attack_range)))
        #                 # if attack_range < 2.0:
        #                 #     power_scale *= min(3.0, max(1.0, enemy.radius / unit.radius))
        #                 # power = (unit.health + unit.shield) * attack_dps
        #                 # enemy.attack_power += power * power_scale * 0.001
        #                 #
        #                 #
        #                 # enemy_power_scale = 1.0
        #                 # enemy_power_scale /= max(1.0, 1.0 + (dist_to_enemy-enemy_attack_range*1.2-enemy.movement_speed*1.2+4.0)*0.5/max(1.0, enemy.movement_speed))
        #                 # enemy_power_scale *= min(2.5, max(1.0, enemy.movement_speed/ max(0.1,unit.movement_speed)))
        #                 # if enemy.movement_speed - unit.movement_speed > 0.1:
        #                 #     enemy_power_scale *= min(2.5, max(1.0, enemy_attack_range / max(0.1,attack_range)))
        #                 # if enemy_attack_range < 2.0:
        #                 #     power_scale *= min(3.0, max(1.0, unit.radius / enemy.radius))
        #                 # enemy_power = (enemy.health + enemy.shield) * enemy_dps
        #                 # unit.enemy_attack_power += enemy_power * enemy_power_scale * 0.001 * 0.9 #The 0.9 factor is an optimism factor that reduce enemy power level
        #
        #                 # TODO: a lot
        #
        #         unit.got_enemies = got_enemies


        #process units - main cycle
        for mem in self.friendly_memory.values:
            if mem.enemy_in_range_count > 0:
                await self.process_micro_unit(mem)
            else:
                self.process_unit_tactics(mem.unit)




    def process_unit_tactics(self, unit : Unit):

        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.OVERLORD]:
            #These units don't do tactics
            return

        if self.tactic == MicroAgentC2.TACTIC_DEFEND:
            #TODO:implement this
            pass
        elif self.tactic == MicroAgentC2.TACTIC_ATTACK:
            if unit.type_id is UnitTypeId.QUEEN:
                return # Don't "attack" with queens (yet)
            #We do not attack with certain units
            # TODO: improve this tactic A LOT!
            # TODO: make sure there are other units to go with, not alone
            if not self.enemy_structures:
                #just go towards enemy start location
                #TODO: rather target in this order: enemy_natural -> enemy_ramp -> enemy_start
                #TODO: drone scouts would be better!
                self.do(unit.attack(self.enemy_start_locations[0]))
            else:
                target = self.enemy_structures.closest_to(unit)
                self.do(unit.attack(target.position))

        elif self.tactic == MicroAgentC2.TACTIC_TRAIN_1:
            self.do(unit.attack(self.enemy_location_0))
        else:
            raise NotImplementedError


    async def process_micro_unit(self, mem : UnitMemory):
        unit : Unit = mem.unit

        if not unit.is_active:
            return
        if mem.ignore_count > 0:
            mem.ignore_count -= 1
            return

        attack_target : Unit = None
        attack_target_mem :UnitMemory = None
        best_pri = -1.0

        # TODO: deal with OL using a different "process" in time - specialization! (this is just a stop-gap)
        if unit.type_id is UnitTypeId.OVERLORD:
            # non-attacking
            from_enemy = self.enemy_units.closest_to(unit)
            pos: Point2 = unit.position
            target_position = pos.towards(from_enemy, -5.0)
            self.do(unit.move(target_position))
            return

        unit_hp = (unit.health + unit.shield) / (unit.health_max + unit.shield_max)


        #Calculate additional RADAR stuff: (relative to friendly units in area)
        for u2 in self.units:
            if mem.position._distance_squared(u2.position) < 100.0:

                dist_to_friend = unit.distance_to(u2) - unit.radius - u2.radius

                s = determine_slice_nr(mem.position, u2.position)
                mem.radar[s,0] = min(mem.radar[s,0], dist_to_friend)
                mem.radar[s,2] += 1 #scale somehow?


        #First create the general inputs that helps the unit decide against ALL enemies
        general_inputs = np.zeros(42)
        general_inputs[0] = unit_hp
        general_inputs[1] = 1.0 if unit.is_cloaked or unit.is_burrowed else 0.0
        general_inputs[2] = min(1.0, mem.speed2 / 6.0)
        if self.is_zerg:
            general_inputs[3] = 1.0 if self.has_creep(unit) else 0.0

        general_inputs[4] = min(1.0, unit.weapon_cooldown / 5.0)

        general_inputs[5] = unit.energy / 200.0


        #This loop is to decide on attack targets
        enemy_mem : UnitMemory
        for enemy_mem in self.enemy_memory.values:
            if enemy_mem.missing:
                #only consider currently visible enemy units for attack targets
                #The rest are used for flee/move/tactics
                continue
            enemy : Unit = enemy_mem.unit
            if enemy.is_hallucination or enemy.is_snapshot or enemy.is_blip or not enemy.is_visible:
                #attacking these is useless?
                continue

            network_inputs = np.copy(general_inputs)

            enemy_hp = (enemy.health + enemy.shield) / (max(1, enemy.health_max + enemy.shield_max))
            network_inputs[8] = enemy_hp

            #Ranged based information:
            dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
            attack_range = unit.air_range if enemy.is_flying else unit.ground_range
            if attack_range <= 0 or dist_to_enemy >= 10.0: #TODO: make this 15.0!
                continue #can't attack this enemy
            #TODO: there is a range related to dist and speed where we don't consider an enemy for attack anymore even if within 15.0 units??

            enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
            #dps = unit.air_dps if enemy.is_flying else unit.ground_dps
            #enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps

            #enemy already in range
            network_inputs[8] = 1.0 if dist_to_enemy <= attack_range else 0.0
            # 1.0 if enemy is in range, else scales down towards 0.0 based on this units speed
            network_inputs[9] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - attack_range)/max(0.1, unit.movement_speed) )
            # The reverse for the enemy
            network_inputs[10] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - enemy_attack_range)/max(0.1, enemy.movement_speed) )

            #How many of our units can attack this unit more or less?
            network_inputs[11] = min(enemy_mem.can_attack_count / 8.0, 1.0)
            #How many targeted this previously?
            network_inputs[12] = min(enemy_mem.attacking_previous_range / 8.0, 1.0)
            network_inputs[13] = min(enemy_mem.attacking_previous_melee / 8.0, 1.0)
            #How many is targeting it this tick?
            network_inputs[14] = min(enemy_mem.attack_count_range / 8.0, 1.0)
            network_inputs[15] = min(enemy_mem.attack_count_melee / 8.0, 1.0)

            #movement speed and attack range comparisons:
            network_inputs[16] = np.clip((unit.movement_speed - enemy.movement_speed) / 5.0, -1.0, 1.0)
            network_inputs[17] = np.clip((attack_range - enemy_attack_range) / 5.0, -1.0, 1.0)

            #this is a ratio of how easily it is theoretically to escape enemy attack range
            network_inputs[18] = np.clip(1.0 - ((enemy_attack_range - dist_to_enemy) / max(0.1, unit.movement_speed)) , 0.0, 1.0)
            #TODO: how easily for enemy to escape us?

            #ratio of radius:
            network_inputs[20] = np.clip((unit.radius - enemy.radius)/2.0 , -1.0, 1.0)

            #Base on "close" range: 1.0=next to us, 0.0=8+ away
            network_inputs[21] = max(1.0 - dist_to_enemy / 8.0 , 0.0)

            #Is the unit lower or higher than us?
            network_inputs[21] = np.clip(unit.position3d.z - enemy.position3d.z, -1.0, 1.0)

            #energy
            network_inputs[22] = enemy.energy / 200.0

            #cloaked?
            network_inputs[23] = 1.0 if enemy.is_cloaked or enemy.is_burrowed else 0.0

            #some other tags
            network_inputs[25] = 1.0 if enemy.is_ready else 0.0
            network_inputs[26] = 1.0 if enemy.is_detector else 0.0
            network_inputs[24] = 1.0 if enemy.cargo_max > 0 else 0.0
            network_inputs[25] = 1.0 if enemy.is_flying else 0.0
            network_inputs[26] = 1.0 if enemy_mem.is_melee else 0.0

            network_inputs[27] = min(1.0, enemy.buff_duration_remain / 22.0)

            #enemy sight range?
            network_inputs[28] = 0.0 # unsure about this?

            #Banelings is a special case against light units
            network_inputs[29] = 0.5 if enemy_mem.type_id is UnitTypeId.BANELING and unit.is_light and not unit.is_flying else 0.0

            #A ratio of the units dps / units_ehp
            network_inputs[30] = enemy_mem.glass_cannon_ratio

            #was attack target last time? (this helps to stabilize the system a bit, like hysteresis)
            network_inputs[31] = 0.5 if enemy.tag == mem.last_attack_target else 0.0

            #TODO: aoe units?

            #TODO: temporary units?

            #TODO: actual damage?
            # TODO: scale by enemy armour



            #TODO: enemy static priority?
            # TODO: enemy static priority

            #TODO: prevent overkill?
            #TODO: applied damage to prevent overkill


            #TODO: for melee units getting blocked can be bad, so consider actual distances,blocks? (move?)
            #USE in batches: self.client.query_pathings()

            #TODO: bonus damage!!! very important actually!



            # TODO: scale this differently based on various other factors THIS IS WAY TOO SIMPLE AND STUPID!!
            # TODO: too many melee units trying to attack an enemy is not good, how to scale this?

            #TODO: scale for enemy units that is about to expire
            #TODO: enemy units busy warping in?

            #calculate results:
            #TODO: split between melee/range/air networks!
            outputs = self.attack_network.process(network_inputs)
            priority = outputs[0]

            if priority > best_pri:
                best_pri = priority
                attack_target = enemy
                attack_target_mem = enemy_mem

        # TODO: fix drones with specialization that they can defend correctly rather than just flee!
        # Drones should only be pulled in correct amounts
        # Drones should never leave the base area, should always want to return to mining asap
        # Drones should only flee if really in danger also, prefer mining even if semi dangerous
        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]:
            attack_target = None



        #TODO's for RADAR:
        # distance to fog of war
        # distance to cliff/unpathable (for non-flying)
        # distance to higher/lower ground? or something about that
        # enemy/friendly structures! and mineral patches (anything blocking!)
        # can move at all in this direction?
        # distance to creep or out of creep (negative/positive)
        # distance to friendly cargo ship?


        move_pri = np.zeros(8)
        #Process slices for move prioritization:
        for s in range(8):
            inputs = np.copy(mem.radar[s])
            #scale normalizations for network required firstly:
            inputs[0] = min(1.0, inputs[0] * 0.25) #dist 2 closest friendly unit
            inputs[1] = min(1.0, inputs[1] * 0.25) #dist 2 closest enemy
            inputs[2] = min(1.0, inputs[2] / 8) # nr of friendlies in this slice
            inputs[3] = min(1.0, inputs[3] / 8) # nr of enemies in this slice
            inputs[4] = min(1.0, inputs[4] / 8) # melee units facing us in this direction (and in range)
            inputs[5] = min(1.0, inputs[5] / 8) # ranges units facing us in this direction (and in range)
            inputs[6] = min(1.0, inputs[6] / 16) # enemy units that have us in range
            inputs[7] = min(1.0, inputs[7] * 0.25) # how far we can move back and still keep "an" enemy in range
            inputs[8] = min(1.0, inputs[8] * 0.25) # how far we need to move back to escape enemy range

            #TODO: some normalization of highest attack priority target found in this slice direction (from attack network calculation)
            #TODO: some threat prioritization system? ie how dangerous is this slice?
            #TODO: Power projection stuff!!
            #TODO: are we currently moving in this direction
            #TODO: push mechanics of nearby units! (advanced)
            #TODO: AOE information

            #a few general inputs:
            inputs[31] = unit_hp
            inputs[30] = 1.0 if mem.is_melee else 0.0
            inputs[29] = 1.0 if unit.is_cloaked or unit.is_burrowed else 0.0
            if self.is_zerg:
                inputs[28] = 1.0 if self.has_creep(unit) else 0.0
            inputs[27] = min(1.0, unit.weapon_cooldown / 5.0)
            inputs[26] = mem.speed2 # current speed


            # Find results from network:
            outputs = self.move_network.process(inputs)
            move_pri[s] += outputs[0] # priority to move in this direction!
            move_pri[(s + 4) % 8] += outputs[1] # priority to run away - ie move in opposite direction


        #TODO: if unit wants to attack enemy outside range convert it to a move priority!!!

        #TODO: move priority decisions!
        # The general idea is that if move_pri >= 1.0 then we move in that direction
        # maybe also move if attack priority < 0.0 ?
        # note: it might take a while for the genetic algorithm to spit out >= 1.0 priorities.. maybe not the best idea?
        move_pri2 = np.zeros(8)
        for s in range(8):
            move_pri2[s] = move_pri[s] + (move_pri[(s-1)%8] + move_pri[(s+1)%8])*0.9 + (move_pri[(s-2)%8] + move_pri[(s+2)%8])*0.7

        best_slice = move_pri2.argmax()
        move_pri = move_pri2[best_slice]
        if not mem.is_melee and unit.weapon_cooldown > 0.5:
            move_pri *= 1.5 #boost move priority for stutter stepping on range units


        #move or attack?
        #TODO: flee!

        if move_pri > 1.0 or best_pri < 0.0:
            if self.debug:
                self.draw_debug_line(unit, unit.position + slice_delta[best_slice], (50,255,50))

            self.do(unit.move(unit.position + slice_delta[best_slice]))

        elif attack_target and best_pri >= 0.0:
            if self.debug:
                self.draw_debug_line(unit, attack_target, (255, 50, 0))

            self.do(unit.attack(attack_target))

            #update last_attack target for next round
            mem.last_attack_target = attack_target.tag

            # update attack counts on the enemy (this greatly helps with focus fire adjustments)
            if mem.is_melee:  # attacking_count_range
                attack_target_mem.attack_count_melee += 1
            else:
                attack_target_mem.attack_count_range += 1

            # TODO: if weapon_cooldown is zero and enemy is in range then add to enemy a counter of the amount of damage that will be done
            # TODO: THEN use this to prevent overkill damage!


    async def process_micro_unit_old(self, unit : Unit, enemy_list : Units):
        attack_target = None
        best_pri = -1.0
        flee_pri = -1.0 # If this ends up positive normally the unit will attempt to flee
        run_away_pri = 0.0
        power_diff = 0.0
        enemy_count = 0


        enemy_x = np.zeros(len(enemy_list), dtype=float)
        enemy_y = np.zeros(len(enemy_list), dtype=float)
        enemy_threat = np.zeros(len(enemy_list), dtype=float)

        #TODO: deal with OL using a different "process" in time - specialization! (this is just a stop-gap)
        if unit.type_id is UnitTypeId.OVERLORD:
            # non-attacking
            from_enemy = enemy_list.closest_to(unit)
            pos: Point2 = unit.position
            target_position = pos.towards(from_enemy, -5.0)
            self.do(unit.move(target_position))
            return

        # TODO: protoss - consider shields also?
        # TODO: scale flee_pri based on damage taken recently


        unit_hp = (unit.health+unit.shield)/(unit.health_max+unit.shield_max)


        general_inputs = np.zeros(42)
        general_inputs[0] = unit_hp
        #general_inputs[1] = lost_hp

        #weapon cool down
        general_inputs[4] = min(1.0, unit.weapon_cooldown / 5.0)
        #general_inputs[5] = 1.0 if unit.ground_range > 0.5 or unit.air_range > 0.5 and unit.weapon_cooldown == 0 else 0.0

        #nr of enemies facing us?
        #general_inputs[6] = max(unit.enemy_facing_melee / 6.0 , 1.0)
        #general_inputs[7] = max(unit.enemy_facing_range / 12.0 , 1.0)


        enemy : Unit
        for e_index,enemy in enumerate(enemy_list.closer_than(10.0, unit)):
            #create new inputs list for network:


            enemy_x[e_index] = enemy.position.x
            enemy_y[e_index] = enemy.position.y

            #Attacking or running away from these is mostly pointless:
            if enemy.is_hallucination or enemy.type_id in [UnitTypeId.LARVA, UnitTypeId.EGG]:
                continue

            # Can we attack this enemy?
            can_attack = unit.can_attack_air if enemy.is_flying else unit.can_attack_ground
            if not can_attack:
                continue

            enemy_count += 1

            network_inputs = np.copy(general_inputs)
            #scale priority by enemy hp levels (kill the weaker ones first)

            enemy_hp = (enemy.health+enemy.shield)/(max(1,enemy.health_max+enemy.shield_max))
            network_inputs[16] = enemy_hp


            #Ranged based information:
            dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
            attack_range = unit.air_range if enemy.is_flying else unit.ground_range
            enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
            #dps = unit.air_dps if enemy.is_flying else unit.ground_dps
            #enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps

            #1.0 if enemy is in range, else scales down towards 0.0 based on this units speed
            network_inputs[17] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - attack_range)/max(0.1, unit.movement_speed) )
            # The reverse for the enemy
            network_inputs[18] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - enemy_attack_range)/max(0.1, enemy.movement_speed) )


            #How many of our units can attack this unit more or less?
            network_inputs[19] = min(enemy.can_attack_count / 8.0, 1.0)

            network_inputs[20] = 0.0 #reserved

            # How many units is currently already targeting this target
            #TODO: this should actually be based on what happened last tick? (but that won't work well with
            # Rather count how many units have this as previous target - need memory system implemented first!
            network_inputs[21] = min(enemy.attacking_count_range / 8.0, 1.0)
            network_inputs[22] = min(enemy.attacking_count_melee / 8.0, 1.0)

            # Add here 1.0 if this was it's previously chosen target
            network_inputs[23] = 0.0 #reserved
            network_inputs[24] = 0.0 #reserved

            #movement speed and attack range comparisons:
            network_inputs[25] = np.clip((unit.movement_speed - enemy.movement_speed) / 5.0, -1.0, 1.0)
            network_inputs[26] = np.clip((attack_range - enemy_attack_range) / 5.0, -1.0, 1.0)

            #this is a ratio of how easily it is theoretically to escape enemy attack range
            network_inputs[27] = np.clip(1.0 - ((enemy_attack_range - dist_to_enemy) / max(0.1, unit.movement_speed)) , 0.0, 1.0)


            #ratio of radius:
            network_inputs[28] = np.clip((unit.radius - enemy.radius)/2.0 , -1.0, 1.0)

            #TODO: must be able to attack enemy (ground to air, air to ground etc)


            #TODO: for melee units getting blocked can be bad, so consider actual distances
            #USE in batches: self.client.query_pathings()

            #TODO: bonus damage!!! very important actually!

            #TODO: consider preferred attack
            #TODO: enemy static priority
            #TODO: scale by enemy armour

            #TODO: enemy energy


            # TODO: scale this differently based on various other factors THIS IS WAY TOO SIMPLE AND STUPID!!
            # TODO: too many melee units trying to attack an enemy is not good, how to scale this?


            #attacking count (adjust priorities if other units has picked this already as target)
            #TODO: !!!! I've removed this whole attack count section - see C1

            #TODO: applied damage to prevent overkill


            #TODO: scale for enemy units that is about to expire
            #TODO: enemy units busy warping in?

            #Power comparisons
            #power_diff += enemy.attack_power - unit.enemy_attack_power

            # Process enemy attack ranges vs our health and our range
            #attack_range = unit.air_range if enemy.is_flying else unit.ground_range
            #if lost_hp > 0.2: #and dist_to_enemy < enemy_attack_range:
            #    #TODO: should be based on enemy threat level also, no point fleeing from non-scary units
            #    #TODO: ideally should check the enemies enemy.facing
            #    if (enemy_attack_range - dist_to_enemy) < unit.movement_speed * 0.3:
            #        flee_pri += 0.15
            #    else:
            #        flee_pri -= 0.07



            #If melee unit is being attacked by 2 or more other melee units it's usually time to leave:
            if attack_range < 2.0 and dist_to_enemy < enemy_attack_range and enemy_attack_range < 2.0 and enemy.movement_speed - unit.movement_speed < 1.0:
                #TODO: look at enemy facing angle
                #TODO: improve this!!
                pass
                #attack_inputs[8] = 1.0


            #Being inside enemy range distance normally means running away is a waste of time:


            # Consider moving away if we can out-range the enemy



            #TODO: avoid AOE!! (big!)

            #baneling incoming?
            if enemy.type_id == UnitTypeId.BANELING and unit.is_light and dist_to_enemy < 4.0 and not unit.is_flying:
                pass
                #attack_inputs[12] = 1.0


            #TODO: avoid getting one-shot by enemies

            #calculate results:
            #TODO: split between melee/range/air networks!
            outputs = self.attack_network.process(network_inputs)
            priority = outputs[0]
            flee_pri = max(flee_pri, outputs[1])
            enemy_threat[e_index] = outputs[2]
            run_away_pri += np.clip(outputs[3], -0.5, 0.5)

            if priority > best_pri:
                best_pri = priority
                attack_target = enemy



        #TODO: remove here the stuff to try fix it so that 1/2 zerglings can attack a baneling


        #Consider fleeing based on power difference
        #power_diff /= enemy_count
        #if power_diff < -0.0: # If power diff is negative we are probably in trouble!
        #    #TODO: implement this system on another way?
        #    pass
        #    #flee_pri -= power_diff

        #combine flee and run_away:
        #flee_pri = max(flee_pri, run_away_pri)

        #The following units never flee
        #if unit.type_id in [UnitTypeId.LOCUSTMP, UnitTypeId.INFESTEDTERRAN, UnitTypeId.AUTOTURRET] or unit.is_hallucination:
        #    flee_pri = 0

        #TODO: fix drones with specialization that they can defend correctly rather than just flee!
        # Drones should only be pulled in correct amounts
        # Drones should never leave the base area, should always want to return to mining asap
        # Drones should only flee if really in danger also, prefer mining even if semi dangerous
        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]:
            attack_target = None


        # For now only attack:
        if attack_target:
            if self.debug:
                 self.client.debug_line_out(unit, attack_target, (255,50,0))

            self.do(unit.attack(attack_target))

            #update attack counts on the enemy (this greatly helps with focus fire adjustments)
            if attack_range >= 2.5 or unit.is_flying:  # attacking_count_range
                attack_target.attacking_count_range += 1
            else:
                attack_target.attacking_count_melee += 1

            #TODO: if weapon_cooldown is zero and enemy is in range then add to enemy a counter of the amount of damage that will be done
            # TODO: THEN use this to prevent overkill damage!


        #TODO: if attack target is more than X outside attack range it should count as a move command rather than attack?
        #
        # if attack_target and (flee_pri <= 1.0) and (best_pri > 0.0):
        #     #print(f"Attacking target : pri = {best_pri}")
        #     if self.debug:
        #         self.client.debug_line_out(unit, attack_target, (255,50,0))
        #
        #     self.do(unit.attack(attack_target))
        #
        #
        #     if attack_range >= 2.5 or unit.is_flying:  # attacking_count_range
        #         attack_target.attacking_count_range += 1
        #     else:
        #         attack_target.attacking_count_melee += 1
        #
        # elif flee_pri >= 1.0:
        #     #print(f"Fleeing : pri = {flee_pri}")
        #     #TODO: improve further - it should probably run away for more than just 1 step
        #     #TODO: position improvement should come in here as well?
        #     pos = unit.position
        #     e_index += 1
        #     thread_pos = Point2((np.average(enemy_x[:e_index], weights=enemy_threat[:e_index]), np.average(enemy_y[:e_index],weights=enemy_threat[:e_index])))
        #     target_position = pos.towards(thread_pos, -6.0)
        #     if self.debug:
        #         self.client.debug_line_out(unit, target_position)
        #     self.do(unit.move(target_position))