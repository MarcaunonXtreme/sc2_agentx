
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
from sc2.position import Point2, Point3
from sc2.units import Units
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM

import pickle

race_supply = {
    Race.Zerg : UnitTypeId.OVERLORD,
    Race.Terran : UnitTypeId.SUPPLYDEPOT,
    Race.Protoss : UnitTypeId.PYLON
}


class CreationTask:

    TYPE_STRUCTURE=1
    TYPE_MORPH_STRUCTURE = 2
    TYPE_ADDON = 3
    TYPE_UNIT = 4
    TYPE_MORPH_UNIT = 5
    TYPE_RESEARCH = 6

    def __init__(self, creation_type, target_unit_id = None, worker_tag = None, location_hint = 0, location = None, research_id = None, factory_type_id = None):
        self.creation_type = creation_type #indicate what type of thing we creating
        self.target_unit_id : UnitTypeId= target_unit_id #the unit type id for what we creating
        self.research_id = research_id # For TYPE_RESEARCH only
        self.worker_tag = worker_tag #worker to use (only for TYPE_STRUCTURE)
        self.egg_tag = None #the unit in training - used by TYPE_UNIT and TYPE_MORPH_UNIT
        self.location_hint = location_hint #location hint can influence things
        self.location : Point2 = location #location to make this if TYPE_STRUCTURE
        self.done : bool = False # Set to true when task is done and should be removed
        self.building_tag = None # Tag of building once it exists (TYPE_STRUCTURE + TYPE_MORPH_STRUCTURE) [For TYPE_ADDON this is set to the add-on itself]
        self.ability_id  = None #ability id used by worker to actually create the structure (Ability id used to create this thing)
        self.unit_location = None # For zerg Unit creation
        self.unit_timeout : int = 0 # Used by zerg unit creation
        self.factory_type_id = factory_type_id # Used by TYPE_UNIT if produced from a specific type of building (e.g. Barracks)


class MyBase:
    def __init__(self, bot, location, units : Units):
        assert isinstance(location, Point2)
        self.agent :sc2.BotAI  = bot
        self.location = location
        assert self.location in self.agent.expansion_locations
        self.worker_shortage = 4
        self.gas_buildings = Units([],bot)
        for u in units:
            assert u.distance_to(self.location) < 10.0

    #TODO: Make this a cached property somehow?
    @property
    def townhall(self) -> sc2.Optional[Unit]:
        if self.agent.townhalls:
            th : Unit = self.agent.townhalls.closest_to(self.location)
            if th.distance_to(self.location) < 4.0:
                return th
        return None

    @property
    def mineral_field(self) -> list:
        result = []
        for u in self.agent.expansion_locations[self.location]:
            if u.is_mineral_field:
                result.append(u)
        return result

    @property
    def mineral_field1(self) -> sc2.Optional[Unit]:
        mf = self.mineral_field
        if mf:
            return mf[0]
        else:
            return None

    @property
    def gas_field(self) -> list:
        result = []
        for u in self.agent.expansion_locations[self.location]:
            if u.is_vespene_geyser:
                result.append(u)
        return result

    def closest_mineral_field(self, location) -> Unit:
        result = None
        best = 1000.0
        for m in self.mineral_field:
            assert isinstance(m, Unit)
            m_loc : Point2 = m.position
            dist = m_loc.distance_to(location)
            if dist < best:
                best = dist
                result = m
        return result

    def empty_geyser(self, gas_buildings : Units):
        self.refresh_gas_buildings(gas_buildings)
        for g in self.gas_field:
            # If no existing gas building is close buy then we can use this one!
            if not self.gas_buildings:
                return g
            if self.gas_buildings.closest_distance_to(g) > 3.5:
                return g
        return None

    def refresh_gas_buildings(self, gas_buildings : Units):
        self.gas_buildings = gas_buildings.filter(lambda bb: bb.distance_to(self.location) < 10.0)
        if len(self.gas_buildings) > len(self.gas_field):
            print("Warning: Base has more gas buildings than geysers?!")


class BaseAgentA1(sc2.BotAI):

    LOCATION_HINT_NONE = 0
    LOCATION_HINT_RAMP = 1
    LOCATION_HINT_NATURAL = 2
    LOCATION_HINT_PROXY = 3
    LOCATION_HINT_EXPAND = 4




    def __init__(self):
        super(BaseAgentA1,self).__init__()
        self.debug = False
        self.structure_tasks = deque()
        self.tagged_workers = [] #TODO!!!
        self.is_zerg = False
        self.my_bases = []
        self.next_base_to_balance = 0

        self.new_structures = []
        self.new_units = []

        self.queen_inject_targets = {} #queen_tags -> hatchery_tags
        self.hatch_queens = {} # hatch_tags -> queen_tags

    async def on_start(self):
        #print(">on_start<")
        self.is_zerg = (self.race == sc2.Race.Zerg)
        print(f"Find start expansion : {self.start_location}")
        for exp in self.expansion_locations:
            print(f" exp : {exp}")
            if self.start_location.distance_to(exp) < 7.5:
                print("found home base")
                self.my_bases.append(MyBase(self,exp,self.expansion_locations[exp]))
        assert len(self.my_bases) > 0
        assert len(self.my_bases) == 1

        # Set game step here:
        self._client.game_step = 2

    def already_pending(self, unit_type: sc2.Union[UpgradeId, UnitTypeId]) -> int:

        if isinstance(unit_type, UpgradeId):
            return self.already_pending_upgrade(unit_type)

        #Add tasks that is busy but not yet started
        task_count = 0
        t : CreationTask
        for t in self.structure_tasks:
            if t.target_unit_id == unit_type:
                task_count += 1
        if task_count > 0:
            return task_count

        #the rest should just do for units being trained then.
        ability = self._game_data.units[unit_type.value].creation_ability
        return self._abilities_all_units[ability]

    async def create_upgrade(self, research_id : UpgradeId):
        assert isinstance(research_id, UpgradeId)

        assert research_id in UPGRADE_RESEARCHED_FROM

        self.structure_tasks.append(CreationTask(CreationTask.TYPE_RESEARCH,research_id=research_id, factory_type_id=UPGRADE_RESEARCHED_FROM[research_id]))

        self.process_research(self.structure_tasks[-1])

    async def create_unit(self, unit_id : UnitTypeId):
        #TODO: handle morphs - Like Overseer
        assert isinstance(unit_id, UnitTypeId)

        if unit_id == UnitTypeId.QUEEN:
            self.structure_tasks.append(CreationTask(CreationTask.TYPE_UNIT, unit_id, factory_type_id=UnitTypeId.HATCHERY))
        elif self.is_zerg:
            #all other zerg units is morph/larva
            self.structure_tasks.append(CreationTask(CreationTask.TYPE_UNIT, unit_id))
        else:
            #find factory for protoss/terran units:
            #TODO: fix for things that have multiple sources (warp/gate)
            self.structure_tasks.append(CreationTask(CreationTask.TYPE_UNIT, unit_id, factory_type_id=UNIT_TRAINED_FROM[unit_id][0]))

        self.process_unit(self.structure_tasks[-1])

    async def create_structure(self, building_id : UnitTypeId, location_hint):
        assert location_hint == 0 #others not yet supported
        assert isinstance(building_id, UnitTypeId)

        #TODO: handle morphs - like Lair
        #TODO: handle addons (reactors/techlab)

        location = await self.find_structure_placement(building_id, location_hint)
        assert location

        # TODO: only select valid workers!
        #w : Unit
        dist = 10000.0
        for ww in self.workers.filter(lambda w: (w.is_collecting or w.is_idle) and  (w.tag not in self.unit_tags_received_action) and (w.tag not in self.tagged_workers)):
            d = ww.distance_to(location)
            if d < dist:
                worker = ww
                dist = d
        assert worker
        self.tagged_workers.append(worker.tag)

        self.structure_tasks.append(CreationTask(CreationTask.TYPE_STRUCTURE, target_unit_id=building_id, worker_tag=worker.tag, location_hint=location_hint, location=location))

        self.process_structure(self.structure_tasks[-1])


    async def on_step(self, iteration: int):
        if iteration == 0:
            # Split workers
            self.split_drones()
            await self.chat_send("Hello from Marcaunon's BO Bot version 0.1 (gg)")

        for task in self.structure_tasks:
            if task.creation_type in [CreationTask.TYPE_STRUCTURE, CreationTask.TYPE_ADDON, CreationTask.TYPE_MORPH_STRUCTURE]:
                self.process_structure(task)
            elif task.creation_type in [CreationTask.TYPE_UNIT, CreationTask.TYPE_MORPH_UNIT]:
                self.process_unit(task)
            elif task.creation_type is CreationTask.TYPE_RESEARCH:
                self.process_research(task)

            if task.done:
                print("Removing completed task")
                self.structure_tasks.remove(task)
                break # Not sure how to do this better?

        self.new_structures = []
        self.new_units = []

    def reserve_resources(self, minerals, vespene):

        if minerals >= 0:
            self.minerals -= minerals
        if vespene >= 0:
            self.vespene -= vespene



    def find_structure(self, task : CreationTask):
        #TODO: improve this by rather using the on_building_construction_started event overide
        structure: Unit
        for structure in self.structures:
            if (structure.type_id == task.target_unit_id) and (structure.build_progress < 1.0) and (structure.distance_to(task.location) < 3):
                return structure
        return None

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        for task in self.structure_tasks:
            if task.creation_type == CreationTask.TYPE_RESEARCH and task.research_id == upgrade:
                print("SUCCESS: research completed")
                task.done = True


    def process_research(self, task : CreationTask):
        if task.done:
            return

        if task.building_tag:
            # Already started probably!
            building : Unit = self.structures.find_by_tag(task.building_tag)
            if building:
                for order in building.orders:
                    if order.ability.id == task.ability_id:
                        #print("research in progress")
                        return
                print("WARNING: research not being done or failed?")
            else:
                print("WARNING: research structure destroyed")
                task.building_tag = None
        else:
            cost = self.calculate_cost(task.research_id)
            if self.minerals >= cost.minerals and self.vespene >= cost.vespene:
                #can research now, find the place to start it
                #TODO: deal with the hatchery/lair/hive problem here for zerg
                s : Unit
                for s in self.structures.filter(lambda ss: ss.is_idle and ss.type_id == task.factory_type_id and ss.tag not in self.unit_tags_received_action):
                    print(f"Starting RESEARCH : {task.research_id}")
                    action = s.research(task.research_id)
                    task.ability_id = action.ability
                    self.do(action, subtract_cost=True)
                    task.building_tag = s.tag
                    return

                self.reserve_resources(cost.minerals, cost.vespene)

            else:
                self.reserve_resources(cost.minerals, cost.vespene)

        assert task.creation_type == CreationTask.TYPE_RESEARCH

    async def on_unit_created(self, unit: Unit):
        #print(f"new unit: {unit}")
        task : CreationTask
        # TODO: implement timing information here to be more accurate! (else this can just be a different unit that was created?)
        for task in self.structure_tasks:
            if task.creation_type in [CreationTask.TYPE_UNIT, CreationTask.TYPE_MORPH_UNIT] and task.target_unit_id == unit.type_id:
                if self.is_zerg and not task.factory_type_id:
                    if task.unit_location and task.unit_location.distance_to(unit.position) < 5.0:
                        print("success: Unit creation completed!")
                        task.done = True
                elif task.factory_type_id:
                    if task.building_tag and task.unit_location and task.unit_location.distance_to(unit.position) < 5.0:
                        print("success: Unit training completed!")
                        task.done = True

        if unit.type_id == UnitTypeId.QUEEN:
            #Try to assign the queen to empty hatchery
            self.assign_queen(unit)



    def process_unit(self, task:CreationTask):
        if task.done:
            return

        assert task.creation_type == CreationTask.TYPE_UNIT

        if self.is_zerg and not task.factory_type_id:

            if task.unit_location:
                #we have a location where it is morphing more or less

                #Check if it busy somewhere?
                #TODO: optimize this better?
                for unit in self.units:  # type: Unit
                    if unit.distance_to(task.unit_location) < 1.5:
                        for order in unit.orders:
                            if order.ability.id == task.ability_id:
                                #still in production egg or larva or something
                                #print(f"Unit in production currently... {unit}")
                                task.unit_timeout = 18
                                return

                task.unit_timeout -= 1
                if task.unit_timeout <= 0:
                    print("WARNING: Unit creation from larva failure!")
                    task.unit_location = None

            else:
                # not larva yet so we haven't started it
                cost = self.calculate_cost(task.target_unit_id)
                supply_cost = self.calculate_supply_cost(task.target_unit_id)
                if self.minerals >= cost.minerals and self.vespene >= cost.vespene and self.supply_left >= supply_cost:
                    larva = self.larva.filter(lambda ll: ll.is_idle and not ll.tag in self.unit_tags_received_action)
                    if larva:
                        larva : Unit = larva[0] #TODO: find larva closest to main base?
                        print(f"Starting training Larva into unit loc:{larva.position}")
                        action = larva.train(task.target_unit_id)
                        task.ability_id = action.ability
                        self.do(action, subtract_cost=True, subtract_supply=True)
                        task.unit_location = larva.position
                        task.unit_timeout = 18 # It takes some amount of time for the egg to appear it seems :/
                    else:
                        #not available larva atm
                        # TODO: reserve also the supply!!!
                        self.reserve_resources(cost.minerals, cost.vespene)
                else:
                    #Can not afford yet
                    #TODO: reserve also 1 larva!
                    #TODO: reserve also the supply!!!
                    self.reserve_resources(cost.minerals, cost.vespene)


        elif task.factory_type_id:
            # Building from a factory of some kind
            if task.building_tag:
                # building tag means its in production or done
                building :Unit = self.structures.find_by_tag(task.building_tag)
                if building:

                    for order in building.orders:
                        if order.ability.id == task.ability_id:
                            #in production still
                            task.unit_timeout = 18
                            return

                    task.unit_timeout -= 1
                    if task.unit_timeout <= 0:
                        print("WARNING: Unit production failure :(")
                        task.building_tag = None
                else:
                    print("WARNING: Building was destroyed! unit lost!")
                    task.building_tag = None
            else:
                cost = self.calculate_cost(task.target_unit_id)
                supply_cost = self.calculate_supply_cost(task.target_unit_id)
                if self.minerals >= cost.minerals and self.vespene >= cost.vespene and self.supply_left >= supply_cost:
                    #can afford now, find a building
                    s : Unit
                    for s in self.structures:
                        type_id = s.type_id
                        if type_id in [UnitTypeId.LAIR, UnitTypeId.HIVE]:
                            type_id = UnitTypeId.HATCHERY
                        if s.is_ready and type_id == task.factory_type_id and len(s.orders) == 0:
                            #found empty structure, lets go!
                            action = s.train(task.target_unit_id)
                            task.ability_id = action.ability
                            self.do(action, subtract_cost=True, subtract_supply=True)
                            task.building_tag = s.tag
                            task.unit_location = s.position
                            task.unit_timeout = 18

                    #No factory available yet!
                    # TODO: reserve supply also
                    self.reserve_resources(cost.minerals, cost.vespene)
                else:
                    #TODO: reserve supply also
                    self.reserve_resources(cost.minerals, cost.vespene)

        else:
            #TODO: P/T
            raise NotImplementedError

    async def on_building_construction_started(self, unit: Unit):
        task : CreationTask
        for task in self.structure_tasks:
            if task.creation_type in [CreationTask.TYPE_STRUCTURE, CreationTask.TYPE_MORPH_STRUCTURE, CreationTask.TYPE_ADDON] and not task.building_tag and task.target_unit_id == unit.type_id:
                if unit.position.distance_to(task.location) < 3 and task.ability_id:
                    task.building_tag = unit.tag

    async def on_building_construction_complete(self, unit: Unit):
        task: CreationTask
        for task in self.structure_tasks:
            if task.creation_type in [CreationTask.TYPE_STRUCTURE, CreationTask.TYPE_MORPH_STRUCTURE, CreationTask.TYPE_ADDON] and task.target_unit_id == unit.type_id and unit.tag == task.building_tag:
                print("success: building completed")
                task.done = True

                if unit.type_id in [UnitTypeId.HATCHERY, UnitTypeId.NEXUS, UnitTypeId.COMMANDCENTER]:
                    #set rally point for workers to local minerals:
                    rally = self.mineral_field.closest_to(unit)
                    self.do(unit(AbilityId.RALLY_WORKERS, rally))


    def process_structure(self, task : CreationTask):

        if task.done:
            return

        assert task.creation_type == CreationTask.TYPE_STRUCTURE

        worker = self.workers.find_by_tag(task.worker_tag)

        #TODO: periodically (6 seconds?) check if nearer worker can be selected?
        if task.building_tag is None:
            #Not yet in actual progress:
            if worker is None:
                #Lost the worker but no building was started?
                #TODO: find a new worker
                print("WARNING: Lost worker before could build structure")
                task.done = True
                return

        #TODO: periodically.. (3 seconds?) recheck building placement? and deal with blocks?

        if task.building_tag is None:
            #Not yet building: move drone / build-it etc.

            distance = worker.distance_to(task.location)
            cost = self.calculate_cost(task.target_unit_id)

            if distance < 1.8:
                # close now! - build or patrol
                if self.minerals >= cost.minerals and self.vespene >= cost.vespene:
                    print("Building now")
                    action = worker.build(task.target_unit_id, task.location)
                    task.ability_id = action.ability
                    self.do(action, subtract_cost=True)
                else:
                    #print("Patrolling")
                    self.do(worker.patrol(task.location))
                    self.reserve_resources(cost.minerals, cost.vespene)

            else:

                time = distance / 2.8 #average worker speed

                # Note: worker = 40 min/minute approx = 0.6 minerals/second
                minerals_rate = len(self.workers) * 0.64 # TODO: should only count actual workers busy mining!
                vespene_rate = 0 #TODO: do this for Gas also!

                reserve_minerals = cost.minerals - minerals_rate * time
                reserve_vespene = cost.vespene - vespene_rate * time

                if (reserve_minerals > self.minerals + 10) or (reserve_vespene > self.vespene + 5):
                    # do nothing else now
                    #print(f"Not moving:  distance: {distance} , time: {time} , reserve: {reserve_minerals} , actual:{self.minerals}")
                    pass
                else:
                    #print(f"Moving towards location, distance: {distance} , time: {time}, reserve: {reserve_minerals}, actual:{self.minerals}")
                    self.do(worker.move(task.location))

                self.reserve_resources(reserve_minerals, reserve_vespene)
        else:

            #track building until complete
            #TODO: Terran: scv attacked/killed?
            #TODO: cancel logic if building under attack
            structure = self.structures.find_by_tag(task.building_tag)
            if not structure:
                #TODO: don't cancel task, reset status to try again.
                print("WARNING: Building disappeared, destroyed?")
                task.building_tag = None
                return


    #async def on_unit_destroyed(self, unit_tag):
        #TODO: Use this for buildings destroyed that wasn't completed!
        #TODO: Use this to trigger building replacements
        #TODO: Use this to notice if morphed units was destroyed
        #TODO: Use this in terran if scv destroyed while building
        #pass


    def find_next_gas_location(self):
        base: MyBase
        for base in self.my_bases:
            g : Unit = base.empty_geyser(self.gas_buildings)
            if g:
                print(f"Found location for gas building: {g} {g.position}")
                return g
        return None

    async def find_next_expansion_location(self):
        loc = await self.get_next_expansion()
        self.my_bases.append(MyBase(self,loc,self.expansion_locations[loc]))
        return loc

    #TODO: lotsa improvements and upgrades required!
    async def find_structure_placement(self, building_id, location_hint):
        # lets just support zerg for now
        assert location_hint == 0  # others not yet supported


        if building_id in [UnitTypeId.EXTRACTOR, UnitTypeId.REFINERY, UnitTypeId.ASSIMILATOR]:
            # GAS building!
            return self.find_next_gas_location()

        if building_id in [UnitTypeId.HATCHERY, UnitTypeId.NEXUS, UnitTypeId.COMMANDCENTER]:
            #Town hall!
            #TODO: actually listen to location_hint!!
            return await self.find_next_expansion_location()


        # this is all the spots we can "place" that has creep.
        allowed = self.game_info.placement_grid.data_numpy
        if self.is_zerg:
            allowed *= self.state.creep.data_numpy

        if isinstance(building_id, UnitTypeId):
            ability_id = self._game_data.units[building_id.value].creation_ability
        else:
            ability_id = building_id

        #This does a random search around the base currently, not great but it's something and can probably fit a few buildings
        while True:
            possible_positions = []
            while len(possible_positions) < 8:
                loc = Point2((int(self.start_location.x) + random.randint(-13,13), int(self.start_location.y) + random.randint(-13,13)))
                if np.all(allowed[loc.y-1:loc.y+2 , loc.x-1:loc.x+2 ]):
                    possible_positions.append(loc)
                    #print(f"Searching loc = {loc}")

            res = await self._client.query_building_placement(ability_id, possible_positions)
            possible = [p for r, p in zip(res, possible_positions) if r == sc2.ActionResult.Success]
            if possible:
                print("Found location!")
                return possible[0]
            print("None possible")

        return None



    def supply_in_production(self):
        #TODO: add townhalls in production!
        return self.already_pending(race_supply[self.race]) * 8


    #attempts to build supply x1
    async def build_one_supply(self):
        if self.race == Race.Zerg:
            await self.create_unit(UnitTypeId.OVERLORD)
            return True
        elif self.race == Race.Protoss:
            await self.create_structure(UnitTypeId.PYLON, self.LOCATION_HINT_NONE)
            return True
        elif self.race == Race.Terran:
            await self.create_structure(UnitTypeId.SUPPLYDEPOT, self.LOCATION_HINT_NONE)
            return True
        else:
            raise EnvironmentError

    def refresh_base_gas_buildings(self):
        for base in self.my_bases:
            base.refresh_gas_buildings(self.gas_buildings)

    def balance_gas_workers(self, remove_gas = False):
        self.refresh_base_gas_buildings()

        base : MyBase
        for base in self.my_bases:
            for g in base.gas_buildings.ready:
                if g.surplus_harvesters == 0 and remove_gas == False:
                    continue
                if remove_gas or g.surplus_harvesters > 0:
                    #remove a worker
                    local_workers = self.workers.filter(lambda ww: ww.order_target == g.tag and (not ww.is_carrying_vespene))
                    if local_workers:
                        self.do(local_workers[0].gather(base.closest_mineral_field(local_workers[0])))
                elif g.surplus_harvesters < 0:
                    # add a workers mining minerals not carrying atm
                    min_tags = {m.tag for m in base.mineral_field}
                    local_workers = self.workers.filter(lambda ww: ww.order_target in min_tags and (not ww.is_carrying_minerals))
                    if len(local_workers) > 4:
                        worker0 = local_workers.closest_to(g)
                        self.do(worker0.gather(g))

    def find_closest_base(self, location, must_be_ready = True) -> MyBase:
        best = 1000.0
        result = None
        for base in self.my_bases:
            if must_be_ready:
                if not base.townhall or not base.townhall.is_ready:
                    continue
            dist = base.location.distance_to(location)
            if dist < best:
                best = dist
                result = base
        return result

    def find_closest_minerals(self, worker):
        assert isinstance(worker, Unit)
        base : MyBase = self.find_closest_base(worker)
        if not base:
            return None
        return base.closest_mineral_field(worker)

    def find_my_base(self, location) -> MyBase:
        for base in self.my_bases:
            if base.location.distance_to(location) < 5.0:
                return base
        print(f"Warning: could not find my base close to: {location}")
        return None

    @property
    def worker_shortage(self):
        result = 0
        for base in self.my_bases:
            result += base.worker_shortage
        return result

    def balance_mineral_workers(self):
        self.next_base_to_balance += 1
        if self.next_base_to_balance >= len(self.my_bases):
            self.next_base_to_balance = 0


        base : MyBase = self.my_bases[self.next_base_to_balance]
        #print(f">>balancing base: {base.location}")
        if not base.townhall:
            #print("No townhall yet!")
            base.worker_shortage = 0
            return #No town hall? probably destroyed
        if not base.townhall.is_ready:
            base.worker_shortage = 4
            return #not yet ready for mining
        th :Unit = base.townhall

        if th.surplus_harvesters <= 0:
            #Base need workers, nothing to do but remember this
            base.worker_shortage = abs(th.surplus_harvesters)
        elif th.surplus_harvesters > 0:
            #print(f"Base has {th.surplus_harvesters} to many workers! ")
            base.worker_shortage = -th.surplus_harvesters
            # find nearest other base that is ready and needs workers.
            next_th = self.townhalls.filter(lambda bb: bb.is_ready and bb.surplus_harvesters < 0)
            if next_th:
                next_th = next_th.closest_to(th)
            else:
                #print("No other base available 4 transfer")
                return
            assert isinstance(next_th,Unit)
            next_base : MyBase= self.find_my_base(next_th)
            if next_base:
                target = next_base.closest_mineral_field(th)

                #Move some workers
                min_tags = {m.tag for m in base.mineral_field}
                local_workers = self.workers.filter(lambda ww: ww.order_target in min_tags and not ww.is_carrying_minerals)
                transfer_amount = min(th.surplus_harvesters, -next_th.surplus_harvesters, len(local_workers))
                print(f"Transferring {transfer_amount} workers now")
                for i in range(0,transfer_amount):
                    worker0 : Unit = local_workers[i]
                    self.do(worker0.gather(target))

                #update shortages:
                base.worker_shortage = 0
                next_base.worker_shortage -= transfer_amount


    #This assigns a new queen to closest open hatchery on creation
    def assign_queen(self, queen : Unit):
        #tries to assign a new queen
        assert queen.type_id == UnitTypeId.QUEEN
        for th in self.townhalls.closer_than(15, queen):
            if th.tag not in self.hatch_queens:
                self.hatch_queens[th.tag] = queen.tag
                self.queen_inject_targets[queen.tag] = th.tag
                return

    # When a queen died..
    #TODO: link and test this!
    def on_queen_destroyed(self , queen_tag):
        if queen_tag in self.queen_inject_targets:
            del self.queen_inject_targets[queen_tag]
            for key in self.hatch_queens:
                if self.hatch_queens[key] == queen_tag:
                    del self.hatch_queens[key]
                    break


    #This will try to inject queens as best possible
    def queen_injects(self):

        #Find list of hatcheries without queens first:

        #since the units list if longer it is more efficient to search that firstly:
        free_queens : Units = Units([], self)
        queen : Unit
        for queen in self.units.filter(lambda uu: uu.type_id == UnitTypeId.QUEEN and uu.energy >= 25 and uu.is_idle):
            if queen.tag in self.queen_inject_targets:
                hatch_tag = self.queen_inject_targets[queen.tag]
                hatchery = self.townhalls.find_by_tag(hatch_tag)
                if hatchery:
                    #Inject now!
                    #TODO: don't inject if hatchery already has more than X larva
                    #print("Injecting!")
                    self.do(queen(AbilityId.EFFECT_INJECTLARVA, hatchery))
                else:
                    #hatchery destroyed?
                    del self.queen_inject_targets[queen.tag]
                    del self.hatch_queens[hatch_tag]
            else:
                free_queens.append(queen)
        #Assign any more qeeuns for injecting
        if free_queens:
            for hatch in self.townhalls.filter(lambda th: th.tag not in self.hatch_queens):
                queen = free_queens.closest_to(hatch)
                self.hatch_queens[hatch.tag] = queen.tag
                self.queen_inject_targets[queen.tag] = hatch.tag


    #split drones on step 1
    def split_drones(self):
        assert self.my_bases
        minerals = self.my_bases[0].mineral_field
        index = 0
        for worker in self.workers:
            if index < len(minerals):
                self.do(worker.gather(minerals[index]))
                index += 1


    def draw_debug_line(self, p0: sc2.Union[Unit, Point2], p1: sc2.Union[Unit, Point2], color=None):
        if isinstance(p0, Unit):
            p0 = p0.position
        if isinstance(p1, Unit):
            p1 = p1.position
        p0 : Point3 = Point3((p0.x, p0.y, self.get_terrain_z_height(p0)+0.2))
        p1 : Point3 = Point3((p1.x, p1.y, self.get_terrain_z_height(p1)+0.2))
        self.client.debug_line_out(p0,p1,color)
