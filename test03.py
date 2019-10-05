
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit


from sc2.constants import UnitTypeId

from sc2.ids.ability_id import AbilityId

from MicroAgentC1 import MicroAgentC1

from buildOrder import *

import time


#TestBot 3 is specifically for micro testing, it will use debug abilities heavily
class TestBot3(MicroAgentC1):

    def __init__(self):
        super(TestBot3,self).__init__()

        self.tactic = MicroAgentC1.TACTIC_ATTACK
        self.debug = True

    def get_pos(self) ->Point2:
        pos = self.game_info.map_center
        self.game_info.start_locations[0] = pos

        if self.player_id == 1:
            x = pos.x +  20
        else:
            x = pos.x - 20

        return Point2((int(x),int(pos.y)))

    async def scenario1(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        # 5 marines only
        # This helps to verify they are focus firing sensibly
        await self.client.debug_create_unit([[UnitTypeId.MARINE, 5, pos, self.player_id]])


    async def scenario2(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        # 10 zerglings vs 10 zerglings
        # This helps to verify they are focus firing sensibly
        await self.client.debug_create_unit([[UnitTypeId.ZERGLING, 10, pos, self.player_id]])

    async def scenario3(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        # 8v8 zealots
        # This helps to verify they are focus firing sensibly
        await self.client.debug_create_unit([[UnitTypeId.ZEALOT, 8, pos, self.player_id]])

    async def scenario4(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        # 8v8 zealots
        # This helps to verify they are focus firing sensibly
        if self.player_id == 1:
            await self.client.debug_create_unit([[UnitTypeId.STALKER, 4, pos, self.player_id]])
        else:
            await self.client.debug_create_unit([[UnitTypeId.ROACH, 12, pos, self.player_id]])

    async def scenario5(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)



        if self.player_id == 1:
            #await self.client.debug_create_unit([[UnitTypeId.SPAWNINGPOOL, 1, pos, self.player_id]])
            #await self.client.debug_upgrade()
            await self.client.debug_create_unit([[UnitTypeId.ZERGLING, 16, pos, self.player_id]])
        else:
            await self.client.debug_create_unit([[UnitTypeId.STALKER, 4, pos, self.player_id]])


    async def scenario6(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        if self.player_id == 1:
            await self.client.debug_create_unit([[UnitTypeId.MARINE, 5, pos, self.player_id]])
        else:
            # await self.client.debug_create_unit([[UnitTypeId.SPAWNINGPOOL, 1, pos, self.player_id]])
            # await self.client.debug_upgrade()
            await self.client.debug_create_unit([[UnitTypeId.ZERGLING, 8, pos, self.player_id]])


    async def scenario7(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)

        #Test if we can correctly attack baneling and not lose all the lings
        if self.player_id == 1:
            await self.client.debug_create_unit([[UnitTypeId.ZERGLING, 4, pos, self.player_id]])
        else:
            await self.client.debug_create_unit([[UnitTypeId.BANELING, 1, pos, self.player_id]])

    async def scenario8(self):
        pos : Point2 = self.get_pos()
        await self.client.move_camera_spatial(pos)


        await self.client.debug_create_unit([[UnitTypeId.ZERGLING, 6, pos, self.player_id]])
        await self.client.debug_create_unit([[UnitTypeId.BANELING, 2, pos, self.player_id]])
        self.client.debug_tech_tree()


    ###Things to test still:
    ## ZvZ: (before anything really advanced)
    # Banelings and zerglings
    # Roach v Roach
    # vs Spines
    # Queens and Roach (for healing)
    # Hydra+Roach (positioning)
    # Ultralisks
    # Mutalisk vs Hydralisk
    # Drones versus zerglings
    # Drones versus banelings
    # Corruptors versus mutalisk
    # broodlords vs anything
    # Air units vs spore crawlers
    #
    ## TvT (non-advanced)
    #
    # Marine vs Marine
    #
    ## PvP
    #
    # Zealot vs Zealot
    # Adept's vs Zealots
    # Drones vs Adept



    async def on_step(self, iteration: int):

        if iteration % 220 == 0:
            #first kill all previous units:
            await self.client.debug_kill_unit(self.units)
            #Start "a" scenario
            await self.scenario6()


        #Call base agent step first
        #This takes care of some low level stuff first at highest priority
        t0 = time.perf_counter_ns()
        await super(TestBot3,self).on_step(iteration)
        t1 = time.perf_counter_ns()
        delta_t = t1-t0
        if delta_t > 45454545:
            print(f"WARNING: using too much CPU for real real-time: {delta_t//1000}usec")
        if delta_t > 45454545*4:
            print(f"ERROR: completely blowing the timing budget now!")


for _ in range(3):
    try:
        run_game(maps.get("Flat96"), [
            Bot(Race.Zerg, TestBot3()),
            Bot(Race.Zerg, TestBot3()),
        ], realtime=True , game_time_limit=30.0)
    except:
        print("Game closed with some exception, oh well ?")


