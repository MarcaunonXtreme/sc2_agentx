
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


from MacroAgentB1 import MacroAgentB1

import time

# This level of the agent takes care of micro type stuff
class MicroAgentC1(MacroAgentB1):

    TACTIC_DEFEND = 1
    TACTIC_ATTACK = 2

    def __init__(self, *args):
        super(MicroAgentC1, self).__init__(*args)
        self.tactic = MicroAgentC1.TACTIC_DEFEND
        self.defend_locations = []
        self.previous_hp = {} #unit_tag : previous_HP (friendly units only)
        self.iteration = -1
        self.delta_step_time = 1.0


    async def on_step(self, iteration: int):
        assert iteration == self.iteration+1
        self.iteration = iteration
        await super(MicroAgentC1,self).on_step(iteration)

        self.delta_step_time = self._client.game_step / 22.0

        #if self.tactic == MicroAgentC1.TACTIC_ATTACK:
        #    time.sleep(150e-3)

        #Make a list of all enemies (units and static-D)
        enemy_list = Units([], self) #enemies that can attack ground
        # TODO: air_enemies! #enemies that can attack air
        unit : Unit
        for unit in self.enemy_units.filter(lambda u: u.type_id not in [UnitTypeId.EGG, UnitTypeId.LARVA]):
            unit.attacking_count_melee = 0
            unit.attacking_count_range = 0
            unit.can_attack_count = 0
            unit.attack_power = 0.0

            enemy_list.append(unit)
        for unit in self.enemy_structures.filter(lambda u: u.can_attack_ground or u.can_attack_air):

            unit.attacking_count_melee = 0
            unit.attacking_count_range = 0
            unit.can_attack_count = 0
            unit.attack_power = 0.0

            enemy_list.append(unit)

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
        for i,unit in enumerate(self.units):
            if unit.type_id not in [UnitTypeId.BROODLING, UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.MULE]:
                unit.got_enemies = False
                unit.enemy_can_attack_count = 0.0
                unit.enemy_attack_power = 0.0

                # TODO: currently need to check ALL enemy units. Using buckets over the map will make this much faster

                # TODO: in time need to increase this to 15.0 but for now this is simpler
                got_enemies = False
                if enemy_list:
                    enemy : Unit
                    for enemy in enemy_list.closer_than(10.0, unit):
                        got_enemies = True

                        #TODO: need to check if CAN actually attack!
                        #TODO: should maybe look more than 1 second ahead in distance?
                        # Check if we can attack it?
                        dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
                        attack_range = unit.air_range if enemy.is_flying else unit.ground_range
                        attack_dps = unit.air_dps if enemy.is_flying else unit.ground_dps
                        enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
                        enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps

                        ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy-attack_range)*2.5/unit.movement_speed)
                        enemy.can_attack_count += ratio

                        enemy_ratio = 1.0 / max(1.0, 1.0 + (dist_to_enemy-enemy_attack_range)*2.5/enemy.movement_speed)
                        unit.enemy_can_attack_count += enemy_ratio

                        #TODO: this still ignores energy levels!
                        #TODO: this still ignores armour!
                        #TODO: still ignore upgrades!
                        #TODO: still ignore creep!
                        #TODO: enemies on high ground is more dangerous - also enemies behind chokes like ramps
                        #TODO: still ignore special offsets. example a stalker with blink is worth more. baneling splash is worth more etc.
                        #TODO: the linear scaling of movement_speed and attack_range separately isn't the best unfortunately!
                        #TODO: does not consider upgrades/buffs and all that!

                        power_scale = 1.0
                        power_scale /= max(1.0, 1.0 + (dist_to_enemy-attack_range*1.2-unit.movement_speed*1.2+4.0)*0.5/max(0.5, unit.movement_speed))
                        power_scale *= min(2.5, max(1.0, unit.movement_speed/max(0.1,enemy.movement_speed)))
                        if unit.movement_speed - enemy.movement_speed > 0.1: #Not ideal but not sure how to scale this better currently
                            power_scale *= min(2.5, max(1.0, attack_range / max(0.1,enemy_attack_range)))
                        if attack_range < 2.0:
                            power_scale *= min(3.0, max(1.0, enemy.radius / unit.radius))
                        power = (unit.health + unit.shield) * attack_dps
                        enemy.attack_power += power * power_scale * 0.001


                        enemy_power_scale = 1.0
                        enemy_power_scale /= max(1.0, 1.0 + (dist_to_enemy-enemy_attack_range*1.2-enemy.movement_speed*1.2+4.0)*0.5/max(1.0, enemy.movement_speed))
                        enemy_power_scale *= min(2.5, max(1.0, enemy.movement_speed/ max(0.1,unit.movement_speed)))
                        if enemy.movement_speed - unit.movement_speed > 0.1:
                            enemy_power_scale *= min(2.5, max(1.0, enemy_attack_range / max(0.1,attack_range)))
                        if enemy_attack_range < 2.0:
                            power_scale *= min(3.0, max(1.0, unit.radius / enemy.radius))
                        enemy_power = (enemy.health + enemy.shield) * enemy_dps
                        unit.enemy_attack_power += enemy_power * enemy_power_scale * 0.001 * 0.9 #The 0.9 factor is an optimism factor that reduce enemy power level

                        # TODO: a lot

                unit.got_enemies = got_enemies

        #process units - main cycle
        for i,unit in enumerate(self.units):
            if unit.type_id not in [UnitTypeId.BROODLING, UnitTypeId.LARVA, UnitTypeId.EGG, UnitTypeId.MULE]:

                if unit.got_enemies:
                    await self.process_micro_unit_ground(unit, enemy_list)
                else:
                    self.previous_hp[unit.tag] = (unit.health+unit.shield)/(unit.health_max+unit.shield_max)
                    #No enemies in range, switching to tactics
                    self.process_micro_unit_tactics(unit)



    def process_micro_unit_tactics(self, unit : Unit):

        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.OVERLORD]:
            #These units don't do tactics
            return

        if self.tactic == MicroAgentC1.TACTIC_DEFEND:
            #TODO:implement this
            pass
        elif self.tactic == MicroAgentC1.TACTIC_ATTACK:
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

        else:
            raise NotImplementedError



    async def process_micro_unit_ground(self, unit : Unit, enemy_list : Units):
        attack_target = None
        best_pri = 0.0
        flee_pri = 0.0 # If this ends up positive normally the unit will attempt to flee
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
        prev_hp = self.previous_hp.get(unit.tag, 1.0)
        lost_hp = prev_hp - unit_hp
        if self.iteration % 4 == 0: #TODO: scale this by game_step setup? - this determine hp loss memory!
            self.previous_hp[unit.tag] = unit_hp

        if unit.health_percentage > 0.5:
            lost_hp *= 0.5 # If unit still positive health reduce effect of health lost

        enemy : Unit
        for e_index,enemy in enumerate(enemy_list.closer_than(10.0, unit)):
            enemy_x[e_index] = enemy.position.x
            enemy_y[e_index] = enemy.position.y

            #Attacking or running away from these is mostly pointless:
            if enemy.is_hallucination or enemy.type_id in [UnitTypeId.LARVA, UnitTypeId.EGG]:
                continue

            enemy_count += 1
            priority = 1.0
            dist_to_enemy = unit.distance_to(enemy) - unit.radius - enemy.radius
            attack_range = unit.air_range if enemy.is_flying else unit.ground_range
            enemy_attack_range = enemy.air_range if unit.is_flying else enemy.ground_range
            enemy_dps = enemy.air_dps if unit.is_flying else enemy.ground_dps
            #TODO: must be able to attack enemy (ground to air, air to ground etc)

            #firstly based on distance:
            priority /= max(1.0,(dist_to_enemy-attack_range)*2.0/unit.movement_speed + (enemy.movement_speed - unit.movement_speed)*0.2)
            priority *= max(1.0, 1.0 +(attack_range - dist_to_enemy)*0.5 / attack_range)
            assert priority >= 0.0

            enemy_threat[e_index] = priority * enemy_dps

            #TODO: for melee units getting blocked can be bad, so consider actual distances
            #USE in batches: self.client.query_pathings()

            #TODO: consider bonus dmg
            #TODO: consider preferred attack
            #TODO: enemy static priority
            #TODO: scale by enemy armour

            #scale priority by enemy hp levels (kill the weaker ones first)
            enemy_hp = (enemy.health+enemy.shield)/(enemy.health_max+enemy.shield_max)
            priority *= 1.0 +  (1.0-enemy_hp)*0.3

            #TODO: enemy energy

            # adjust priority slightly based on how many of our units CAN attack this enemy
            priority += min(enemy.can_attack_count / 5, 0.2)

            # TODO: scale this differently based on various other factors THIS IS WAY TOO SIMPLE AND STUPID!!
            # TODO: too many melee units trying to attack an enemy is not good, how to scale this?


            #attacking count (adjust priorities if other units has picked this already as target)
            if attack_range >= 2.5 or unit.is_flying: #attacking_count_range
                #Ranged and flying units can stack quite a lot without problem
                if enemy.attacking_count_range > 0:
                    priority += 0.1

            else:#attacking_count_melee
                #Melee units are more tricky and depends on sizes
                # TODO: improve, this doesn't work very well currently
                ideal_attackers = enemy.radius / unit.radius * 2 #Should these be squared rather? to get real ratio of surface area?
                if enemy.type_id == UnitTypeId.BANELING and enemy.attacking_count_melee > 0:
                    priority -= 1.0 #2 melee attacking banelings is stupid
                elif enemy.attacking_count_melee > 0 and enemy.attacking_count_melee < ideal_attackers:
                    priority += 0.05
                elif enemy.attacking_count_melee > ideal_attackers*2:
                    priority -= 10.0 #way to many already! find something else to do!
                else:
                    priority -= 1.5

            #TODO: applied damage to prevent overkill


            #TODO: scale for enemy units that is about to expire
            #TODO: enemy units busy warping in?

            #Power comparisons
            power_diff += enemy.attack_power - unit.enemy_attack_power

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
            if attack_range < 2.0 and dist_to_enemy < enemy_attack_range and enemy_attack_range < 2.0 and enemy.movement_speed - unit.movement_speed < 1.0 and unit_hp < 0.75:
                #TODO: look at enemy facing angle

                if self.debug:
                    self.client.debug_line_out(unit, enemy)
                #print("Melee unit being attacked by melee?")
                flee_pri += 0.075
                enemy_threat[e_index] += 0.2


            #Being inside enemy range distance normally means running away is a waste of time:
            if (enemy_attack_range - dist_to_enemy) > unit.movement_speed * 0.3:
                flee_pri -= 0.05



            # Consider moving away if we can out-range the enemy
            attack_mid = (attack_range + enemy_attack_range) / 2.0
            if unit.movement_speed - enemy.movement_speed > 0.1 and attack_range - enemy_attack_range > 1.0:
                enemy_threat[e_index] += 0.4
                if dist_to_enemy < enemy_attack_range:
                    flee_pri += 0.2
                elif dist_to_enemy < attack_range:
                    flee_pri += 0.1
            elif enemy.movement_speed - unit.movement_speed > 1.0 and enemy_attack_range - attack_range > 2.0:
                # however if already deep within enemy range it's normally pointless to run
                if dist_to_enemy < attack_mid:
                    flee_pri -= 0.05

            #TODO: avoid AOE!! (big!)

            #baneling incoming?
            if enemy.type_id == UnitTypeId.BANELING and unit.is_light and dist_to_enemy < 4.0 and not unit.is_flying:
                enemy_threat[e_index] += 0.5
                flee_pri = max(1.0, flee_pri)


            #TODO: avoid getting one-shot by enemies

            if priority > best_pri:
                best_pri = priority
                attack_target = enemy




        if attack_target:
            #Additional calculations on this chosen target
            attack_range = unit.air_range if attack_target.is_flying else unit.ground_range
            dist_to_enemy = unit.distance_to(attack_target) - unit.radius - enemy.radius + 1.0

            #Need to allow 1 unit to attack a baneling in melee range therefore reduce fleeing for it
            if attack_target.type_id == UnitTypeId.BANELING and attack_range < 2.5 and (not unit.is_flying) and attack_target.attacking_count_melee == 0:
                flee_pri -= 1.0 #Offset baneling flee priority here



        #Consider fleeing based on power difference
        power_diff /= enemy_count
        if power_diff < -0.0: # If power diff is negative we are probably in trouble!
           flee_pri -= power_diff



        #Consider stutter step:
        if attack_target and unit.movement_speed >= 2:
            #TODO: exclude units here that can't stutter step, like hydralisks! Or jut include units for which this DOES work
            if attack_range > 2.0 and unit.weapon_cooldown and dist_to_enemy < attack_range:
                #TODO: still check if can be blocked?
                #TODO: find a way for the units to stay together and not just split up so much!
                flee_pri += 0.5


        #The following units never flee
        if unit.type_id in [UnitTypeId.LOCUSTMP, UnitTypeId.INFESTEDTERRAN, UnitTypeId.AUTOTURRET] or unit.is_hallucination:
            flee_pri = 0

        #TODO: fix drones with specialization that they can defend correctly rather than just flee!
        # Drones should only be pulled in correct amounts
        # Drones should never leave the base area, should always want to return to mining asap
        # Drones should only flee if really in danger also, prefer mining even if semi dangerous
        if unit.type_id in [UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE]:
            attack_target = None

        if attack_target and (flee_pri <= 0.1) and (best_pri > 0.0):
            #print(f"Attacking target : pri = {best_pri}")
            if self.debug:
                self.client.debug_line_out(unit,attack_target, (255,50,0))
            self.do(unit.attack(attack_target))
            if attack_range >= 2.5 or unit.is_flying:  # attacking_count_range
                attack_target.attacking_count_range += 1
            else:
                attack_target.attacking_count_melee += 1
        elif flee_pri >= 0.1:
            print(f"Fleeing : pri = {flee_pri}")
            #TODO: improve further - it should probably run away for more than just 1 step
            #TODO: position improvement should come in here as well?
            pos = unit.position
            e_index += 1
            thread_pos = Point2((np.average(enemy_x[:e_index], weights=enemy_threat[:e_index]), np.average(enemy_y[:e_index],weights=enemy_threat[:e_index])))
            target_position = pos.towards(thread_pos, -6.0)
            target_position = target_position.towards(self.start_location, 2.0)
            if self.debug:
                self.client.debug_line_out(pos,target_position)
            self.do(unit.move(target_position))