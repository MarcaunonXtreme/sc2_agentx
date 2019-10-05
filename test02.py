
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit

from sc2.constants import UnitTypeId

from sc2.ids.ability_id import AbilityId

import pickle

from MacroAgentB1 import MacroAgentB1

from buildOrder import *


class TestBot2(MacroAgentB1):

    def __init__(self):

        #Simple BO to start with
        bo1 = [BO_Supply(TriggerSupply(14)),
               BO_Gas(TriggerSupply(15)),
              BO_Build(TriggerSupply(16), UnitTypeId.BARRACKS),
              #TODO: reactor when rax done 100%
              #TODO: orbital command when rax done 100%
              BO_Expand(TriggerSupply(19)),
              BO_Build(TriggerSupply(20), UnitTypeId.MARINE, count=2),  #NOTE: currently crashing here
              BO_Supply(TriggerSupply(20)),
              BO_Build(TriggerImmediate(), UnitTypeId.BARRACKS),
              #TODO: oribital when natural is done
              BO_Build(TriggerImmediate(), UnitTypeId.BARRACKS),
              #TODO: tech lab then reactor on rax 2+3
              BO_UnitPriorities(TriggerImmediate(), [UnitTypeId.MARINE]),
              BO_AutoSupply(TriggerImmediate(), True),
              #Build more rax as resources available:
              BO_Build(TriggerResourceCount(125), UnitTypeId.BARRACKS),
              BO_Build(TriggerResourceCount(125), UnitTypeId.BARRACKS),
              BO_Build(TriggerResourceCount(200), UnitTypeId.BARRACKS),
              BO_Build(TriggerResourceCount(250), UnitTypeId.BARRACKS)
              ]


        super(TestBot2,self).__init__(bo1)


    async def on_step(self, iteration: int):
        await super(TestBot2, self).on_step(iteration)


#TODO: why does Flat64 crash??
run_game(maps.get("Simple64"), [
    Bot(Race.Terran, TestBot2()),
    Computer(Race.Random, Difficulty.Easy)
], realtime=True , game_time_limit=360.0)

