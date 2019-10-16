
from MicroAgentC2 import MicroAgentC2


from TrainableAgent import TrainableAgent

from sc2.unit import Unit

from sc2.position import Point2


#TODO: move to other file?
#this class can inherit anything but must eventually inherit sc2.BotAI to be a bot
class BotInTraining(MicroAgentC2, TrainableAgent):
    def __init__(self, master , global_debug, *args):
        MicroAgentC2.__init__(self, *args)
        TrainableAgent.__init__(self)
        self.master  = master

        #disable macro and set training mode tactics for now
        self.disable_macro = True
        self.disable_strategy = True
        self.tactic = MicroAgentC2.TACTIC_TRAIN_1 #TODO: fix this
        self.debug = global_debug

        self.enemy_location_0: Point2 = None

    async def on_start(self):
        assert self.player_id == 1 # Only player 1 can "train"
        self.master.register_player(self)
        self.enemy_location_0 = self.game_info.map_center
        await super(BotInTraining,self).on_start()


    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.master.step0_setup(self)
            return

        if self.master.setup_in_progress:
            #setup is in progress
            await self.master.setup_scenario(self)
        else:
            #Call the normal agent to work
            await super(BotInTraining,self).on_step(iteration)

            #Kill units that ran away:
            killme = []
            u : Unit
            for u in self.units:
                if u.distance_to(self.enemy_location_0) > 36.0:
                    killme.append(u.tag)

            if killme:
                print(f"Killing {len(killme)} units")
                await self.client.debug_kill_unit(killme)

            #Check if scenario ended?
            await self.master.check_scenario_end(self)

    async def on_unit_destroyed(self, unit_tag):
        await super(BotInTraining, self).on_unit_destroyed(unit_tag)
        #if unit_tag == self.death_struct_tag:
        #    self.death_struct_tag = -1

    async def on_building_construction_complete(self, unit: Unit):
        print("New building popped up!!")
        await super(BotInTraining, self).on_building_construction_complete(unit)

    async def on_upgrade_complete(self, upgrade):
        #print(f"Got Upgrade: {upgrade}")
        await super(BotInTraining, self).on_upgrade_complete(upgrade)

