
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
        self.range_attack_network : AgentBrain.Network = None
        self.range_move_network : AgentBrain.Network = None
        self.melee_attack_network : AgentBrain.Network = None
        self.melee_move_network : AgentBrain.Network = None
        self.flying_attack_network : AgentBrain.Network = None
        self.flying_move_network : AgentBrain.Network = None

        self.enemy_memory : Memory = Memory(self, self.enemy_got_upgrades)
        self.friendly_memory : Memory = Memory(self, self.got_upgrades)

    def get_brain(self) -> AgentBrain:
        return self.brain

    def use_brain(self, brain : AgentBrain):
        self.brain = brain
        assert isinstance(self.brain, AgentBrain.AgentBrain)
        #TODO Rather combine this into 1 network!
        #print(f"Agent got a new brain! {self.player_id}")
        self.range_attack_network = brain.get_network(self.race, "range_attack", 42, 2)
        self.range_move_network = brain.get_network(self.race, "range_move", 42, 2, hidden_count=16)
        self.melee_attack_network = brain.get_network(self.race, "melee_attack", 42, 2)
        self.melee_move_network = brain.get_network(self.race, "melee_move", 42, 2, hidden_count=16)
        self.flying_attack_network = brain.get_network(self.race, "flying_attack", 42, 2)
        self.flying_move_network = brain.get_network(self.race, "flying_move", 42, 2, hidden_count=16)


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

            mem.surround_length = 0

            mem.closest_friendly_dist = 10.0
            mem.closest_friendly_tag = 0

            mem.power_projection = 0.0
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

            mem.surround_length = 0

            mem.closest_friendly_dist = 10.0
            mem.closest_friendly_tag = 0

            mem.power_projection = 0.0
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
        #TODO: my own static-D?! (especially for zerg)

        for unit in self.units:
            if unit.type_id not in [UnitTypeId.BROODLING, UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.MULE]:

                mem : UnitMemory = self.friendly_memory.see_unit(unit)

                if not unit.is_active:
                    continue

                mem.enemy_in_range_count = 0
                mem.can_attack_count = 0
                mem.power_projection = 0.0


                mem.radar.fill(0)
                for i in range(8):
                    mem.radar[i, 0] = 20.0 #for closest friendly unit
                    mem.radar[i, 1] = 20.0 #for closest enemy unit

                enemy_centre = [0, 0]

                #Process all enemy units in local area
                enemy : UnitMemory
                for enemy in self.enemy_memory.values:
                    if unit.position._distance_squared(enemy.position) < 100.0: #TODO: make this 15**2

                        enemy_centre[0] += enemy.position.x
                        enemy_centre[1] += enemy.position.y
                        mem.enemy_in_range_count += 1

                        #was target previously?
                        if mem.last_attack_target == enemy.tag:
                            if mem.is_melee:
                                enemy.attacking_previous_melee += 1
                            else:
                                enemy.attacking_previous_range += 1

                        #some unit<>enemy calculations
                        dist_to_enemy = unit.distance_to(enemy.position) - unit.radius - enemy.radius

                        if dist_to_enemy < enemy.closest_friendly_dist:
                            enemy.closest_friendly_dist = dist_to_enemy
                            enemy.closest_friendly_tag = unit.tag
                        mem.closest_enemy_dist = min(mem.closest_enemy_dist, dist_to_enemy)

                        if dist_to_enemy <= 0.5:
                            enemy.surround_length += 2*unit.radius
                            mem.surround_length += 2*enemy.radius

                        #Generate RADAR information
                        s = determine_slice_nr(mem.position, enemy.position)
                        #TODO: also process structures on radar! (as they can block things!)
                        mem.radar[s,1] = min(mem.radar[s,1], dist_to_enemy) #closest enemy unit
                        mem.radar[s,3] += 1 #scale somehow?



                        if enemy.missing == 0: # currently visible enemy we can see

                            #TODO: use actual values that take upgrades/buffs into consideration
                            attack_range = unit.air_range if enemy.unit.is_flying else unit.ground_range
                            enemy_attack_range = enemy.unit.air_range if unit.is_flying else enemy.unit.ground_range

                            #attack_dps = unit.air_dps if enemy.unit.is_flying else unit.ground_dps
                            attack_dps = mem.get_dps_versus(enemy)
                            #enemy_attack_dps = enemy.unit.air_dps if unit.is_flying else enemy.unit.ground_dps
                            enemy_attack_dps = enemy.get_dps_versus(mem)

                            # Update can_attack_count - useful for managing attack priorities
                            # Note: simplified:
                            #ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy - attack_range) * 5.0 / max(mem.movement_speed, 1.0))
                            #enemy.can_attack_count += ratio
                            enemy.can_attack_count += 1.0 if dist_to_enemy < (attack_range + 0.25) else 0.0
                            

                            # see if enemy is facing us?
                            if dist_to_enemy < enemy_attack_range + 0.5:
                                angle = math.atan2(unit.position.y - enemy.position.y, unit.position.x - enemy.position.x) - enemy.facing
                                angle = min(math.fabs(angle), math.fabs(angle - math.pi*2))
                                if angle < 0.030: #Not sure how find to make this
                                    if enemy.is_melee:
                                        #TODO: scale this by some kind of threat calculation?
                                        if dist_to_enemy < enemy_attack_range + 0.5:
                                            mem.radar[s,4] += 1
                                    else:
                                        if dist_to_enemy < enemy_attack_range + 0.2:
                                            mem.radar[s,5] += 1

                            #we in enemy range in general?
                            if dist_to_enemy < enemy_attack_range + 0.1:
                                mem.radar[s,6] += 1

                            #7 = how far can we move back and still have enemy in range?
                            mem.radar[s,7] = max(mem.radar[s,7], attack_range - dist_to_enemy)
                            #8 = 
                            mem.radar[s,8] = 0

                            #TODO: calculate power projections against memory only units also?
                            #TODO: still need to use real: attack speeds, attack ranges
                            #TODO: still need to consider unitThreats.py information
                            #TODO: improve this more in other ways
                            #TODO: visually test that this works somehow?
                            #Short range power projection: (only versus visible units? for now?)
                            power_ratio = np.clip(1.0 - max(0,dist_to_enemy - (attack_range+mem.movement_speed*2))/(mem.movement_speed*2) , 0.0, 1.0)
                            power = (25+mem.health+mem.shield) * (1 + attack_dps + unit.energy*0.1)

                            enemy_power_ratio = np.clip(1.0 - max(0,dist_to_enemy - (enemy_attack_range+enemy.movement_speed*2))/(enemy.movement_speed*2) , 0.0, 1.0)
                            enemy_power = (25+enemy.health+enemy.shield) * (1 + enemy_attack_dps + enemy.unit.energy*0.1)

                            mem.power_projection += enemy_power * enemy_power_ratio # power projected against this unit
                            mem.radar[s, 10] += enemy_power * enemy_power_ratio # power projected against from this angle
                            enemy.power_projection += power * power_ratio


                if mem.enemy_in_range_count:
                    mem.enemy_centre = Point2((enemy_centre[0] / mem.enemy_in_range_count, enemy_centre[1] / mem.enemy_in_range_count))
                else:
                    mem.enemy_centre = self.enemy_start_locations[0]

        #delete memory of any friendly units that died previously (can maybe do this via a callback??)
        self.friendly_memory.process_missing_friendly_units()



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

        mem.delta_power_projection = 0.0

        if not unit.is_active:
            return
        if mem.ignore_count > 0:
            mem.ignore_count -= 1
            return

        #TODO: upgrade this more? (for unit specializations!)
        #Find correct networks for this unit
        if not mem.attack_network or not mem.move_network:
            if unit.is_flying:
                mem.attack_network = self.flying_attack_network
                mem.move_network = self.flying_move_network
            elif mem.is_melee:
                mem.attack_network = self.melee_attack_network
                mem.move_network = self.melee_move_network
            else:
                mem.attack_network = self.range_attack_network
                mem.move_network = self.range_move_network


        attack_target : Unit = None
        attack_target_mem :UnitMemory = None
        best_pri = -1.0
        attack_target_in_range = False

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
        mem.friend_in_range_count = 0
        friend_centre = [0,0]
        for u2 in self.units:
            if mem.position._distance_squared(u2.position) < 100.0:

                friend_centre[0] += u2.position.x
                friend_centre[1] += u2.position.y
                mem.friend_in_range_count += 1

                dist_to_friend = unit.distance_to(u2) - unit.radius - u2.radius

                s = determine_slice_nr(mem.position, u2.position)
                mem.radar[s,0] = min(mem.radar[s,0], dist_to_friend)
                mem.radar[s,2] += 1 #scale somehow?

        if mem.friend_in_range_count:
            mem.friendly_centre = Point2( (friend_centre[0] / mem.friend_in_range_count, friend_centre[1] / mem.friend_in_range_count) )
        else:
            mem.friendly_centre = mem.position

        #First create the general inputs that helps the unit decide against ALL enemies
        general_inputs = np.zeros(42)
        general_inputs[0] = unit_hp
        general_inputs[1] = 1.0 if unit.is_cloaked or unit.is_burrowed else 0.0
        general_inputs[2] = min(1.0, mem.speed2 / 6.0)
        if self.is_zerg:
            general_inputs[3] = 1.0 if self.has_creep(unit) else 0.0


        general_inputs[4] = unit.energy / 200.0


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
            network_inputs[7] = enemy_hp

            #Ranged based information:
            dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
            #TODO: update to use REAL ranges!

            attack_range = unit.air_range if enemy.is_flying else unit.ground_range
            if attack_range <= 0 or dist_to_enemy >= 15.0: 
                continue #can't attack this enemy
            
            # If enemy to far for this unit currently then considering it for attacking is pointless at this time.
            if dist_to_enemy > 1.0 + attack_range + 4*mem.movement_speed:
                continue


            enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
            #dps = unit.air_dps if enemy.is_flying else unit.ground_dps
            #enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps

            #enemy already in range
            network_inputs[8] = 1.0 if dist_to_enemy <= attack_range+0.1 else 0.0
            # 1.0 if enemy is in range, else scales down towards 0.0 based on this units speed
            network_inputs[9] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - attack_range)/max(0.1, mem.movement_speed) )
            # The reverse for the enemy
            network_inputs[10] = 1.0 / max(1.0, 1.0 + (dist_to_enemy - enemy_attack_range)/max(0.1, enemy_mem.movement_speed) )

            #How many of our units can attack this unit more or less?
            network_inputs[11] = min(enemy_mem.can_attack_count / 8.0, 1.0)
            #How many targeted this previously?
            network_inputs[12] = min(enemy_mem.attacking_previous_range / 8.0, 1.0)
            network_inputs[13] = min(enemy_mem.attacking_previous_melee / 8.0, 1.0)
            #How many is targeting it this tick?
            #network_inputs[14] = min(enemy_mem.attack_count_range / 8.0, 1.0)
            #network_inputs[15] = min(enemy_mem.attack_count_melee / 8.0, 1.0)

            #movement speed and attack range comparisons:
            #TODO: use REAL movement speeds! (ZERGLING)
            network_inputs[16] = np.clip((mem.movement_speed - enemy_mem.movement_speed) / 5.0, -1.0, 1.0)
            #TODO: use real attack range!
            network_inputs[17] = np.clip((attack_range - enemy_attack_range) / 5.0, -1.0, 1.0)

            #this is a ratio of how easily it is theoretically to escape enemy attack range
            #network_inputs[18] = np.clip(1.0 - ((enemy_attack_range - dist_to_enemy) / max(0.1, mem.movement_speed)) , 0.0, 1.0)
            #TODO: how easily for enemy to escape us?

            #ratio of radius:
            network_inputs[20] = np.clip((unit.radius - enemy.radius)/2.0 , -1.0, 1.0)

            #Base on "close" range: 1.0=next to us, 0.0=8+ away
            network_inputs[21] = max(1.0 - dist_to_enemy / 8.0 , 0.0)

            #Is the unit lower or higher than us?
            network_inputs[22] = np.clip(unit.position3d.z - enemy.position3d.z, -0.5, 0.5)

            #energy
            network_inputs[23] = enemy.energy / 200.0

            #cloaked?
            network_inputs[24] = 1.0 if enemy.is_cloaked or enemy.is_burrowed else 0.0

            #some other tags
            network_inputs[25] = 1.0 if enemy.is_ready else 0.0
            network_inputs[26] = 1.0 if enemy.is_detector else 0.0
            network_inputs[27] = 1.0 if enemy.cargo_max > 0 else 0.0
            network_inputs[28] = 1.0 if enemy.is_flying else 0.0
            network_inputs[29] = 1.0 if enemy_mem.is_melee else 0.0

            # ??
            #network_inputs[27] = min(1.0, enemy.buff_duration_remain / 22.0)



            #Banelings is a special case against light units
            network_inputs[31] = 0.5 if enemy_mem.type_id is UnitTypeId.BANELING and unit.is_light and not unit.is_flying else 0.0

            #A ratio of the units dps / units_ehp
            network_inputs[32] = enemy_mem.glass_cannon_ratio

            #was attack target last time? (this helps to stabilize the system a bit, like hysteresis)
            network_inputs[33] = 0.5 if enemy.tag == mem.last_attack_target else 0.0

            

            # Dist from enemy centre? (should scale by max, ie identify units that are on the edges)
            #network_inputs[34] = min(1.0, mem.enemy_centre.distance_to(enemy)**2 / mem.enemy_in_range_count / 5.0)

            network_inputs[35]  = min(0.5, enemy_mem.surround_length / (2*math.pi*enemy.radius))

            network_inputs[36] = 1.0 if dist_to_enemy < mem.closest_enemy_dist + 0.35 else 0.0

            network_inputs[37] = 1.0 if unit.tag == enemy_mem.closest_friendly_tag else 0.0

            network_inputs[40] = 1.0 if mem.bonus_dmg_versus(enemy_mem) else 0.0
            if enemy_mem.health > enemy_mem.shield:
                network_inputs[41] = 0.2 * enemy_mem.armor
            else:
                network_inputs[41] = 0.2 * enemy_mem.shield_armor

            #TODO: aoe units?

            #TODO: temporary units?


            #TODO: enemy static priority?
            # TODO: enemy static priority

            #TODO: prevent overkill?
            #TODO: applied damage to prevent overkill

            #TODO: for melee units getting blocked can be bad, so consider actual distances,blocks? (move?)
            #USE in batches: self.client.query_pathings()


            #TODO: scale this differently based on various other factors THIS IS WAY TOO SIMPLE AND STUPID!!

            #TODO: scale for enemy units that is about to expire
            #TODO: enemy units busy warping in?

            #calculate results:
            outputs = mem.attack_network.process(network_inputs)
            priority = outputs[0]

            if priority > best_pri:
                best_pri = priority
                attack_target = enemy
                attack_target_mem = enemy_mem
                attack_target_in_range = (dist_to_enemy <= (attack_range + 1.0 + mem.movement_speed*0.5))


            #some additional calculations for the slice:
            s = determine_slice_nr(mem.position, enemy.position)
            mem.radar[s, 11] += (enemy_mem.power_projection - mem.radar[s, 10])
            mem.delta_power_projection += (enemy_mem.power_projection - mem.power_projection)


        # TODO: fix drones with specialization that they can defend correctly rather than just flee!
        # Drones should only be pulled in correct amounts
        # Drones should never leave the base area, should always want to return to mining asap
        # Drones should only flee if really in danger also, prefer mining even if semi dangerous
        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]:
            attack_target = None


        mem.delta_power_projection_lpf = mem.delta_power_projection_lpf*0.8 + mem.delta_power_projection*0.2

        situation = mem.delta_power_projection - mem.delta_power_projection_lpf

        if situation >= 100.0:
            mem.good_bad = max(0,mem.good_bad + 1)
            mem.attack_mode = True if mem.good_bad >= 3 else mem.attack_mode
        else:
            mem.good_bad = min(0, mem.good_bad - 1)
            mem.attack_mode = False if mem.good_bad <= -10 else mem.attack_mode

        #TODO's for RADAR:
        # distance to fog of war
        # distance to cliff/unpathable (for non-flying)
        # distance to higher/lower ground? or something about that
        # enemy/friendly structures! and mineral patches (anything blocking!)
        # can move at all in this direction?
        # distance to creep or out of creep (negative/positive)
        # distance to friendly cargo ship?


        move_pri = np.zeros(8)

        #TODO: can probably use distance squared to speed this up!
        E = mem.position.distance_to(mem.enemy_centre)
        F = mem.position.distance_to(mem.friendly_centre)

        most_friends = np.argmax(mem.radar[:,2])
        most_enemies = np.argmax(mem.radar[:,3])

        #Process slices for move prioritization:
        for s in range(8):
            dest_position : Point2 = mem.position + (slice_delta[s] * 0.5)

            #inputs = np.copy(mem.radar[s])
            inputs = np.zeros(mem.radar[s].shape)
            mem_radar = mem.radar[s]
            #scale normalizations for network required firstly:
            inputs[0] = min(1.0, mem_radar[0] * 0.25) #dist 2 closest friendly unit
            inputs[1] = min(1.0, mem_radar[1] * 0.25) #dist 2 closest enemy

            inputs[2] = 1.0 if mem_radar[2] else 0.0
            inputs[3] = 1.0 if mem_radar[3] else 0.0
            #inputs[2] = min(1.0, inputs[2] / 8) # nr of friendlies in this slice
            #inputs[3] = min(1.0, inputs[3] / 8) # nr of enemies in this slice

            inputs[4] = min(1.0, mem_radar[4] / 4) # melee units facing us in this direction (and in range)
            inputs[5] = min(1.0, mem_radar[5] / 4) # ranges units facing us in this direction (and in range)

            inputs[6] = 1.0 if mem_radar[6] else 0.0 # enemy has us ranged!

            inputs[7] = 2.0 if mem_radar[7] > mem.movement_speed * 0.2 else 0.0
            #inputs[7] = min(1.0, inputs[7] * 0.25) # how far we can move back and still keep "an" enemy in range
            #inputs[8] = min(1.0, inputs[8] * 0.25) # how far we need to move back to escape enemy range

            inputs[11] = np.clip(mem_radar[11]*0.01,-1.0,1.0) # short range delta power projection

            inputs[12] = 1.0 if s == most_friends and mem_radar[2] else 0.0
            inputs[13] = 1.0 if s == most_enemies and mem_radar[3] else 0.0

            #if inputs[13] > 0:
            #    self.draw_debug_line(mem.position, dest_position, (250, 250, 0))

            # if self.debug:
            #     if inputs[11] >= 0.0:
            #         self.draw_debug_line(mem.position, mem.position + (slice_delta[s] * inputs[11]) , (50,250,50))
            #     else:
            #         self.draw_debug_line(mem.position, mem.position + (slice_delta[s] * -inputs[11]), (250, 50, 50))

            if mem.friend_in_range_count > 0 and mem.enemy_in_range_count > 0:
                E2 = mem.enemy_centre.distance_to(dest_position)
                F2 = mem.friendly_centre.distance_to(dest_position)

                #closer/further from our own centre?
                if abs(F2-F) > 0.6:
                    inputs[16] = np.sign(F - F2) #approach/retreat friendly centre

                if E2-E > 0.6:
                    inputs[17] = E2-E #this is the escape direction, moving away from enemies
                if E-E2 > 0.6:
                    inputs[18] = E-E2 #attack general direction


                # tmpb = (F2-E2) - (F-E)
                # if abs(tmpb) > 0.5:
                #     inputs[18] = np.sign(tmpb) #approach/retreat relative to battle line
                #
                # if inputs[18] > 0:
                #     self.draw_debug_line(mem.position, dest_position, (50, 250, 0))
                # if inputs[18] < 0:
                #     self.draw_debug_line(mem.position, dest_position, (250, 50, 0))
                #
                # if F2-F > 0.7 and abs(tmpb) < 0.2:
                #     inputs[19] = 1.0 #Flanking direction


            #TODO: compare distance from battle line with range to help units align correctly before they engage?
            #TODO: some normalization of highest attack priority target found in this slice direction (from attack network calculation)
            #TODO: some threat prioritization system? ie how dangerous is this slice?
            #TODO: are we currently moving in this direction
            #TODO: push mechanics of nearby units! (advanced)
            #TODO: AOE information

            #a few general inputs:
            inputs[26] = unit_hp
            inputs[27] = 1.0 if unit.is_cloaked or unit.is_burrowed else 0.0
            inputs[28] = 1.0 if self.has_creep(unit) else 0.0
            inputs[29] = min(1.0,mem.surround_length / (2*math.pi*unit.radius))
            inputs[30] = np.sign(situation)  # better/worse situation?

            #inputs[29] = 1.0 if unit.weapon_cooldown else 0.0
            #inputs[30] = mem.speed2 # current speed

            #friendly/enemies in slices next to this one (wider radar)
            # not sure what is best to use? maybe distance rather?
            inputs[34] = 1.0 if mem.radar[(s+1) % 8][2] else 0.0
            inputs[35] = 1.0 if mem.radar[(s-1) % 8][2] else 0.0
            inputs[36] = 1.0 if mem.radar[(s+1) % 8][3] else 0.0
            inputs[37] = 1.0 if mem.radar[(s-1) % 8][3] else 0.0


            # Find results from network:
            outputs = mem.move_network.process(inputs)
            outputs[0] = np.clip(outputs[0],-1.8,1.8)
            move_pri[s] += outputs[0] # priority to move in this direction!
            move_pri[(s + 4) % 8] -= outputs[0] # priority to run away = opposite of this one obviously
            if outputs[1] > 0:
                #Flanking priority
                outputs[1] = min(1.0, outputs[1]*0.25)
                move_pri[(s + 2) % 8] += outputs[1]
                move_pri[(s - 2) % 8] += outputs[1]


        # If attack target out of range transform into a move command in said direction rather
        #attack_target_slice = 0
        if best_pri >= 0.0:
            attack_target_slice = determine_slice_nr(mem.position, attack_target.position)
            if attack_target_in_range:
                move_pri[attack_target_slice] += 0.1
            else:
                move_pri[attack_target_slice] += 1.0 # this will help us get closer to target we want to kill
                if not mem.attack_mode:
                    best_pri = -1
                    attack_target = None

        # Calculate move priority across the 8 directions:
        move_pri2 = np.zeros(8)
        for s in range(8):
            move_pri2[s] = move_pri[s] + (move_pri[(s-1)%8] + move_pri[(s+1)%8])*0.6 + (move_pri[(s-2)%8] + move_pri[(s+2)%8])*0.2

        #remove directions that are not pathable:
        if not unit.is_flying:
            for s in range(8):
                dest_position : Point2 = mem.position + (slice_delta[s] * 0.5)
                if not self.in_pathing_grid(dest_position):
                    move_pri2[s] = -10.0

        best_slice = move_pri2.argmax()
        move_pri = move_pri2[best_slice]

        #if best_slice == attack_target_slice:
            #We moving in direction we want to attack...
        #    pass

        #TODO: flee!

        # decide if we should move the unit?
        if best_pri < 0.0 or (not mem.is_melee and unit.weapon_cooldown and move_pri > 0.25) or (move_pri > 2.0 and not mem.attack_mode): # or (move_pri > 2.4):
            # moving
            #if self.debug:
            #    self.draw_debug_line(unit, unit.position + slice_delta[best_slice], (50,255,50))

            if attack_target and best_pri >= 0.0 and attack_target_slice and best_slice == attack_target_slice:
                #well, might as well move closer to what we want to attack (this avoids running past enemy units)
                self.do(unit.move(attack_target))
            else:
                #move in this general slice direction
                self.do(unit.move(unit.position + slice_delta[best_slice]))

        elif attack_target:
            #attack time!
            #if self.debug:
            #    self.draw_debug_line(unit, attack_target, (255, 50, 0))

            self.do(unit.attack(attack_target))

            #update last_attack target for next round
            mem.last_attack_target = attack_target.tag

            # update attack counts on the enemy (this helps with focus fire adjustments)
            #if mem.is_melee:  # attacking_count_range
            #    attack_target_mem.attack_count_melee += 1
            #else:
            #    attack_target_mem.attack_count_range += 1

            # TODO: if weapon_cooldown is zero and enemy is in range then add to enemy a counter of the amount of damage that will be done
            # TODO: THEN use this to prevent overkill damage!
