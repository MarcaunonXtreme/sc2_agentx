

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit

from sc2.constants import UnitTypeId

from sc2.ids.ability_id import AbilityId

import pickle

from MicroAgentC1 import MicroAgentC1

from buildOrder import *

class TestBot1(MicroAgentC1):

    def __init__(self):

        #This is a simple zerg build setup to start with
        bo1 = [BO_Supply(TriggerSupply(13)),
              BO_Build(TriggerSupply(16),UnitTypeId.SPAWNINGPOOL),
              BO_Gas(TriggerReady(UnitTypeId.SPAWNINGPOOL,50)),
              BO_Supply(TriggerSupply(19)),
              BO_GasHarvesting(TriggerResourceCount(0,96),False),
              BO_Build(TriggerReady(UnitTypeId.SPAWNINGPOOL), UnitTypeId.QUEEN),
              BO_Build(TriggerSupply(21), UnitTypeId.ZERGLING, count=2),
              BO_AutoSupply(TriggerSupply(22),True),
              BO_UnitPriorities(TriggerSupply(22), [UnitTypeId.ZERGLING])
              ]

        #Simple BO to research speed early game (to test things like gas and research
        bo2= [  BO_Build(TriggerSupply(13), UnitTypeId.SPAWNINGPOOL),
                BO_Gas(TriggerImmediate()),
                BO_Supply(TriggerImmediate()),
                BO_Build(TriggerReady(UnitTypeId.SPAWNINGPOOL), UnitTypeId.QUEEN),
                #TODO: maybe 2 or 4 lings for protection here? and scouting?
                BO_AutoSupply(TriggerImmediate(), True),
                BO_GasHarvesting(TriggerResourceCount(0, 96), False),
                BO_Upgrade(TriggerImmediate(), UpgradeId.ZERGLINGMOVEMENTSPEED),
                BO_Build(TriggerImmediate(), UnitTypeId.QUEEN),
                BO_UnitPriorities(TriggerSupply(20),[UnitTypeId.ZERGLING]),
                BO_Expand(TriggerResourceCount(250)),
                BO_AttackAllIn(TriggerSupply(30)),  # not the best trigger but it's a start
                BO_Build(TriggerResourceCount(250), UnitTypeId.QUEEN),
                BO_Build(TriggerResourceCount(300), UnitTypeId.QUEEN),
        ]


        #Simple hatch first BO to see if drone balance and queen stuff can work
        bo3 = [#TODO: extractor trick?
                BO_Expand(TriggerSupply(14)),
                BO_Gas(TriggerImmediate()),
                BO_Build(TriggerSupply(14), UnitTypeId.SPAWNINGPOOL),
                BO_Supply(TriggerImmediate()),
                BO_Build(TriggerReady(UnitTypeId.SPAWNINGPOOL), UnitTypeId.QUEEN),
                BO_AutoSupply(TriggerImmediate(), True),
                BO_GasHarvesting(TriggerResourceCount(0,96),False), # remove drones once we have 100 gas!
                BO_UnitPriorities(TriggerImmediate(), [UnitTypeId.ZERGLING]),
                BO_Build(TriggerSupply(19), UnitTypeId.QUEEN),
                BO_Upgrade(TriggerResourceCount(100,100), UpgradeId.ZERGLINGMOVEMENTSPEED)
        ]

        #Simply test to build queens and see what they can do
        bo4 = [
                BO_Build(TriggerImmediate(), UnitTypeId.SPAWNINGPOOL),
                BO_AutoSupply(TriggerImmediate(), True),
                BO_Build(TriggerReady(UnitTypeId.SPAWNINGPOOL), UnitTypeId.QUEEN),
                BO_Build(TriggerReady(UnitTypeId.SPAWNINGPOOL), UnitTypeId.QUEEN),
        ]

        super(TestBot1,self).__init__(bo2)



    async def on_step(self, iteration: int):

        if iteration == 1:
            #pickle.dump(self.game_info.placement_grid, open("placement.p","wb"))
            #pickle.dump(self.state.creep, open("creep.p", "wb"))
            #pickle.dump(self.state.visibility, open("vis.p", "wb"))
            #pickle.dump(self.game_info.terrain_height, open("height.p", "wb"))
            #pickle.dump(self.game_info.pathing_grid, open("path.p", "wb"))
            print(f"start location: {self.start_location}")

        #Call base agent step first
        #This takes care of some low level stuff first at highest priority
        await super(TestBot1,self).on_step(iteration)

        ### Basic Observations & State updates ###


        ### Macro ###
        self.player_id



run_game(maps.get("Simple64"), [
    Bot(Race.Zerg, TestBot1()),
    Computer(Race.Protoss, Difficulty.VeryHard)
    #Bot(Race.Zerg, TestBot1()),
], realtime=True , game_time_limit=480.0)



#run_game(maps.get("Abyssal Reef LE"), [
#    Bot(Race.Zerg, TestBot1()),
#    Computer(Race.Protoss, Difficulty.Medium)
#], realtime=True , game_time_limit=120.0)

