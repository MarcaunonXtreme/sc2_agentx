
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit

import numpy as np

from sc2.constants import UnitTypeId
import sc2.constants

import random

from collections import deque

from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2

import pickle

from MacroAgentB1 import MacroAgentB1
from MicroAgentC1 import MicroAgentC1

# Base class for Build order start triggers
class BOrderTrigger:

    # Return true if start is possible
    def can_start(self, agent: MacroAgentB1):
        raise NotImplementedError

class TriggerImmediate(BOrderTrigger):
    def can_start(self, agent: MacroAgentB1):
        return True

class TriggerSupply(BOrderTrigger):
    def __init__(self, supply_count):
        self.supply_count : int = supply_count

    def can_start(self, agent: MacroAgentB1):
        if not agent.auto_supply and self.supply_count > agent.supply_cap and agent.supply_in_production() == 0:
            print(f"Warning: triggerSupply supply trigger level > current supply cap! {self.supply_count} > {agent.supply_cap}")
        return agent.supply_used >= self.supply_count


class TriggerReady(BOrderTrigger):
    def __init__(self, building_id, percentage = 100):
        self.building_id = building_id
        self.p = percentage / 100.0 - 0.01
        self.p = np.clip(self.p,0.01,0.99)

    def can_start(self, agent: MacroAgentB1):
        for _ in agent.structures.filter(lambda s: s.type_id == self.building_id and s.build_progress >= self.p):
            return True
        return False

class TriggerWorkerCount(BOrderTrigger):
    pass

class TriggerUnitCount(BOrderTrigger):
    pass

class TriggerResourceCount(BOrderTrigger):
    def __init__(self, minerals, vespene=0):
        self.m = minerals
        self.v = vespene

    def can_start(self, agent: MacroAgentB1):
        return agent.minerals >= self.m and agent.vespene >= self.v


class TriggerGameTime(BOrderTrigger):
    pass

class TriggerDeltaTime(BOrderTrigger):
    pass


# Base class for build orders
class BOrder:

    #initializer
    def __init__(self, trigger ):
        assert isinstance(trigger, BOrderTrigger)
        self.trigger : BOrderTrigger = trigger

    #return true if this build order can start executing
    def can_start(self, agent: MacroAgentB1):
        if self.trigger:
            return self.trigger.can_start(agent)
        else:
            return True

    #execute the build order, return true when done/complete
    async def execute(self, agent: MacroAgentB1):
        raise NotImplementedError


class BO_Supply(BOrder):
    def __init__(self, trigger):
        super(BO_Supply,self).__init__(trigger)

    async def execute(self, agent: MacroAgentB1):
        await agent.build_one_supply()
        return True

class BO_Gas(BOrder):

    def __init__(self, trigger):
        super(BO_Gas,self).__init__(trigger)

    async def execute(self, agent: MacroAgentB1):
        await agent.create_structure(sc2.race_gas[agent.race], agent.LOCATION_HINT_NONE)
        return True

class BO_Expand(BOrder):
    def __init__(self, trigger):
        super(BO_Expand,self).__init__(trigger)

    async def execute(self, agent: MacroAgentB1):
        townHalls = {Race.Zerg: UnitTypeId.HATCHERY , Race.Terran : UnitTypeId.COMMANDCENTER, Race.Protoss : UnitTypeId.NEXUS}
        await agent.create_structure(townHalls[agent.race], agent.LOCATION_HINT_NONE)
        return True


class BO_Build(BOrder):

    def __init__(self, trigger, unit_id : UnitTypeId, location_hint = MacroAgentB1.LOCATION_HINT_NONE, count :int = 1):
        super(BO_Build,self).__init__(trigger)
        self.unit_id : UnitTypeId = unit_id
        self.location_hint = location_hint
        self.count = count
        if self.count > 8:
            print("Note: BO_Build not well optimized really for high counts currently!")


    async def execute(self, agent: MacroAgentB1):
        #first check if this is a "structure" or "unit"

        if sc2.constants.IS_STRUCTURE in agent.game_data.units[self.unit_id.value].attributes:
            assert self.count == 1
            # is structure (like spawning pool)
            print(f"Building a structure {self.unit_id} X {self.count}")
            for _ in range(self.count):
                await agent.create_structure(self.unit_id, self.location_hint)
            return True
        else:
            print(f"Creating a unit {self.unit_id} X {self.count}")
            for _ in range(self.count):
                await agent.create_unit(self.unit_id)
            return True


class BO_UnitPriorities(BOrder):
    def __init__(self, trigger, priorities):
        super(BO_UnitPriorities, self).__init__(trigger)
        self.pri = priorities
        assert isinstance(self.pri,list)
        for u in self.pri:
            assert isinstance(u, UnitTypeId)

    async def execute(self, agent: MacroAgentB1):
        agent.set_unit_priorities(self.pri)
        return True


class BO_Upgrade(BOrder):
    def __init__(self, trigger, upgrade_id):
        super(BO_Upgrade, self).__init__(trigger)
        self.upgrade_id = upgrade_id

    async def execute(self, agent: MacroAgentB1):
        await agent.create_upgrade(self.upgrade_id)
        return True


class BO_SendUnit(BOrder):
    pass

class BO_Creep(BOrder):
    pass

class BO_ExtractorTrick(BOrder):
    pass

class BO_AttackAllIn(BOrder):
    def __init__(self, trigger):
        super(BO_AttackAllIn, self).__init__(trigger)

    async def execute(self, agent: MicroAgentC1):
        agent.tactic = MicroAgentC1.TACTIC_ATTACK
        return True

class BO_ScoutNow(BOrder):
    pass

class BO_OrbitalScan(BOrder):
    pass

class BO_HallucinatePhoenixScout(BOrder):
    pass


class BO_AutoSupply(BOrder):
    def __init__(self,trigger, enable):
        super(BO_AutoSupply,self).__init__(trigger)
        self.enable = enable

    async def execute(self, agent: MacroAgentB1):
        agent.set_auto_supply(self.enable)
        return True

class BO_GasHarvesting(BOrder):
    def __init__(self,trigger, enable):
        super(BO_GasHarvesting,self).__init__(trigger)
        self.enable = enable

    async def execute(self, agent: MacroAgentB1):
        agent.set_gas_harvesting(self.enable)
        return True

class BO_AutoExpand(BOrder):
    pass

class BO_SetTactics(BOrder):
    pass

