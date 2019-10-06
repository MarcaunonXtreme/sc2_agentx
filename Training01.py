
import sc2
from sc2 import run_game, maps, Race #, Difficulty
from sc2.player import Bot #, Computer
from sc2.unit import Unit
from sc2.game_data import  UnitTypeData
from sc2.position import Point2

from sc2.constants import UnitTypeId

from AgentBrain import AgentBrain
from TrainableAgent import TrainableAgent

from MicroAgentC2 import MicroAgentC2


from copy import deepcopy
import random
import numpy as np


global_debug = False

###Scenario control:
## Ultimately we want to play every scenario at least 6 times (for genetic algorithms)
## twice with the agents swapped in both directions
## Then three times do that with different pairs of agents
## At the end of every scenario:
##


def calculate_wealth(self):
    m = 0
    v = 0
    for unit in self.units + self.structures:  # type: Unit
        # only if something can be created: (ie not larva and eggs etc)
        assert isinstance(unit.type_id, UnitTypeId)
        item_id = unit.type_id
        if item_id in [UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.BROODLING, UnitTypeId.CREEPTUMOR,
                       UnitTypeId.CREEPTUMORBURROWED]:
            continue
        if item_id == UnitTypeId.REACTOR:
            m += 50
            v += 50
            continue
        if item_id == UnitTypeId.TECHLAB:
            m += 50
            v += 25
            continue
        unit_data = self._game_data.units[item_id.value]
        creation_ability = unit_data.creation_ability
        if not creation_ability:
            continue
        type_data: UnitTypeData = self.game_data.units.get(item_id.value, None)
        if not type_data:
            continue
        # print(f"Cost {item_id} = {type_data.cost}")
        m += type_data.cost.minerals
        v += type_data.cost.vespene

    # print(f"total Wealth = {m} : {v}")

    return m, v


class TrainingMaster:
    def __init__(self, nr_brains = 20):
        self.players = [None, None]
        self.setup_stage = 0
        self.round = 0
        self.end_time = 90.0
        self.position = [[Point2(),Point2()],[Point2(),Point2()]]
        self.brains = []
        for nr in range(nr_brains):
            self.brains.append(AgentBrain.load(f"agents/agent_{nr}.p"))


    def register_player(self, bot : sc2.BotAI):
        if bot.player_id == 1:
            print("Player 1 registered")
            self.players[0] = bot
        else:
            assert bot.player_id == 2
            print("Player 2 registered")
            self.players[1] = bot

        if self.players[0] is not None and self.players[1] is not None:
            #do start-up things!
            self.calculation_positions()

    @property
    def setup_in_progress(self):
        return self.players[0].setup_stage < 10 or self.players[1].setup_stage < 10



    async def step0_setup(self, agent : sc2.BotAI):
        print("Step 0 setup...")
        # firstly remove all existing units
        await agent.client.debug_kill_unit(agent.units)
        #TODO: fix up starting positions so scouting isn't necessary
        #TODO: on 4-player maps fix this so that the bases gets moved to the corner locations

        #Note: not sure this is really workable?
        if agent.race == Race.Zerg:
            # We create some static D around the hatchery so that the AI can't learn to just target this first or run around or something
            for _ in range(4):
                await agent.client.debug_create_unit([[UnitTypeId.SPINECRAWLER, 1, agent.start_location, agent.player_id]])
                await agent.client.debug_create_unit([[UnitTypeId.SPORECRAWLER, 1, agent.start_location, agent.player_id]])
        elif agent.race == Race.Terran:
            for _ in range(3):
                await agent.client.debug_create_unit([[UnitTypeId.PLANETARYFORTRESS, 1, agent.start_location, agent.player_id]])
                await agent.client.debug_create_unit([[UnitTypeId.MISSILETURRET, 2, agent.start_location, agent.player_id]])
        elif agent.race == Race.Protoss:
            await agent.client.debug_create_unit([[UnitTypeId.PHOTONCANNON, 6, agent.start_location, agent.player_id]])
        else:
            raise NotImplementedError

    def end_map_now(self):
        print("==== ENDING THIS MAP ====")

        #TODO: update this to actually work on networks and note brains!

        for b in self.brains:
            assert b.used == 1 #all brains used once now!

        scores = [b.score for b in self.brains]  #actually the average score to make it fair.

        f = open("train_report.txt","a+")
        f.write("== End of Map ==\r\n")
        f.write(f"SCORES: {scores}\r\n")

        scores.sort(reverse=True)
        cutoff1 = scores[round(len(scores)*0.1)]
        cutoff2 = scores[round(len(scores)*0.3)]
        f.write(f"top 10% score = {cutoff1}\r\n")
        f.write(f"top 30% score = {cutoff2}\r\n")

        top_score = max(scores)
        bot_score = min(scores)

        b : AgentBrain
        for i,b in enumerate(self.brains):
            if b.score == top_score:
                continue #don't remove top scorer ever!
            if b.used <= 0:
                continue #don't delete brains if they never had a chance!

            #TODO: upgrade this to the star system!
            if b.score < cutoff2:
                #Not in top 30%
                self.brains[i] = None
            elif b.score < cutoff1:
                #Not in top 10% = 50% elimination chance
                if np.random.random() < 0.5:
                    self.brains[i] = None

        survived = [b for b in self.brains if b is not None]
        f.write(f"{len(survived)} brains survived\r\n")
        f.close()

        #create new brains by mutating the survivors randomly:
        for i, b in enumerate(self.brains):
            if b is None:
                newb :AgentBrain = deepcopy(random.choice(survived))
                newb.mutate()
                self.brains[i] = newb

        for b in self.brains:
            b.reset_counts()

        print("Saving brains...")
        for nr, b in enumerate(self.brains):
            b.save(f"agents/agent_{nr}.p")

        # TODO: shutdown everything now, mutate and save
        self.round = 0

        #p: sc2.BotAI = self.players[0]
        #p.client.debug_leave()


    def end_scenario_now(self):
        print("=SCENARIO ENDED=")
        end_time = self.players[0].time
        print(f"Scenario ended in {end_time}")
        lost_wealth = []
        for agent in self.players:
            agent.setup_stage = 0
            m, v = calculate_wealth(agent)
            wealth = m + v * 1.5
            #print(f"Player {agent.player_id} end wealth = {wealth}")
            lost_wealth.append(abs(wealth - agent.start_wealth))


        #TODO: adjust also based on time taken
        #TODO: adjust for partial damage?? (not sure this is a good idea?)
        p1_score = lost_wealth[1] - lost_wealth[0]
        #p2_score = lost_wealth[0] - lost_wealth[1]
        print(f"Player 1 score = {p1_score}")
        #print(f"Player 2 score = {p2_score}")

        done = True
        for b in self.brains:
            if not b.used:
                done = False
                break
        if done:
            #all brains have now been used one time
            self.end_map_now()


        ### notes on scoring:
        # with genetic algorithm we just want to know how well an agent did relatively
        # even if the scenario is unfair
        # one way is to play the scenario from both sides with both players and average the scores
        # But what if agents are race specific or other things.
        # Better is to play multiple different agents on the same scenario and then compare to average score.

        #Start new scenario:
        self.round += 1

        #Score the brain used by player 1 only
        b1 : AgentBrain = self.players[0].get_brain()
        #b2 : AgentBrain = self.players[1].get_brain()
        b1.score += p1_score
        #b2.score += p2_score
        #self.players[0].use_brain(b2)
        #self.players[1].use_brain(b1)


    def check_scenario_end(self,agent :sc2.BotAI):
        th : Unit = agent.townhalls[0]
        if th.health_percentage < 0.99:
            #TODO: in advanced mode maybe we can hide a floating CC in the corner of the map to avoid triggering the game ending when the townhall dies?
            print("Townhall damaged - ending scenario")
            self.end_scenario_now()
        elif agent.time >= self.end_time: #1.5 minutes is max time for scenario
            print("Scenario ended due to time limit")
            self.end_scenario_now()
        elif agent.death_struct_tag == -1:
             print("Fallback position destroyed, ending scenario")
             self.end_scenario_now()
        else:
            if len(agent.units) < 10:
                cnt = agent.units.filter(lambda u: u.type_id not in [UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.BROODLING, UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED])
                if len(cnt) <= 0:
                    print("Units lost, ending scenario")
                    self.end_scenario_now()


    def get_pos(self, agent: sc2.BotAI, pos_nr = 0) -> Point2:
        if agent.player_id == 1:
            return self.position[0][pos_nr]
        else:
            return self.position[1][pos_nr]

    def calculation_positions(self):

        centre: Point2 = self.players[0].game_info.map_center

        self.position[0][0] = centre.towards(self.players[0].start_location, 15)
        self.position[0][1] = centre.towards(self.players[0].start_location, 25)

        self.position[1][0] = centre.towards(self.players[1].start_location, 15)
        self.position[1][1] = centre.towards(self.players[1].start_location, 25)

        for i in range(2):
            for j in range(2):
                pos = self.position[i][j]
                self.position[i][j] = Point2((int(pos.x),int(pos.y)))

    async def create_buildings(self, agent: sc2.BotAI):
        pos = self.get_pos(agent, pos_nr=1)

        for u in agent.structures:
            if u.type_id in [UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.GREATERSPIRE, UnitTypeId.FUSIONCORE, UnitTypeId.PYLON, UnitTypeId.FLEETBEACON]:
                await agent.client.debug_kill_unit(u)

        # Note: not sure this is really workable?
        if agent.race == Race.Zerg:
            # We create some static D around the hatchery so that the AI can't learn to just target this first or run around or something
            await agent.client.debug_create_unit([[UnitTypeId.CREEPTUMORBURROWED, 2,pos, agent.player_id]])
            await agent.client.debug_create_unit([[UnitTypeId.GREATERSPIRE, 1, pos, agent.player_id]])
        elif agent.race == Race.Terran:
            await agent.client.debug_create_unit([[UnitTypeId.FUSIONCORE, 1, pos, agent.player_id]])
        elif agent.race == Race.Protoss:
            #await agent.client.debug_create_unit([[UnitTypeId.PYLON, 1, pos, agent.player_id]])
            await agent.client.debug_create_unit([[UnitTypeId.FLEETBEACON, 1, pos, agent.player_id]])
        else:
            raise NotImplementedError


    async def setup_scenario(self, agent :sc2.BotAI):
        assert isinstance(agent, TrainableAgent)
        assert isinstance(agent, sc2.BotAI)
        #print(f"Player {agent.player_id} setup stage = {agent.setup_stage}")
        if agent.setup_stage == 0:
            #load checkpoint:
            if agent.player_id == 1:
                print("== STARTING NEW SCENARIO ==")

            #setup fallback position
            await self.create_buildings(agent)

            if agent.player_id == 1:
                # select new brain for player 1
                chosen = None
                for b in self.brains:
                    if b.used == 0:
                        chosen = b
                        break
                assert chosen
                agent.use_brain(chosen)

            else:
                # player 2 don't get a new brain as it's the protagonist
                pass

            #clear old stuff:
            await agent.client.debug_fast_build()
            if agent.units:
                await agent.client.debug_kill_unit(agent.units)

            #TODO: call agent reset to clear memory and other things?
            #Note: not sure how to clear buildings that was remembered etc?

            agent.setup_stage = 1

        if agent.setup_stage == 1:
            # Wait for all old units to be removed

            if len(agent.units.filter(lambda u: u.type_id not in [UnitTypeId.LARVA, UnitTypeId.EGG])) == 0:
                agent.setup_stage = 2


        if agent.setup_stage == 2:
            agent.setup_stage = 3
            # Enable fast build so that we can quickly up the tech tree etc as necessary

            #make sure all broodlings from destroyed buildings go away
            garbage = agent.units.filter(lambda u: u.type_id in [UnitTypeId.BROODLING, UnitTypeId.BROODLINGESCORT, UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.AUTOTURRET, UnitTypeId.INFESTEDTERRAN, UnitTypeId.LOCUSTMPFLYING, UnitTypeId.LOCUSTMP])
            if garbage:
                await agent.client.debug_kill_unit(garbage)

            #TODO: pick 2 different locations on map each time rather than same locations every time!
            pos = self.get_pos(agent)
            #TODO: implement actual scenarios
            if agent.race == Race.Zerg:
                await agent.client.debug_create_unit([[UnitTypeId.ZERGLING, 12, pos, agent.player_id]])
                #await agent.client.debug_create_unit([[UnitTypeId.ROACH, 2, pos, agent.player_id]])
            elif agent.race == Race.Terran:
                await agent.client.debug_create_unit([[UnitTypeId.MARINE, 6, pos, agent.player_id]])
                await agent.client.debug_create_unit([[UnitTypeId.MARAUDER, 2, pos, agent.player_id]])
            elif agent.race == Race.Protoss:
                await agent.client.debug_create_unit([[UnitTypeId.ZEALOT, 4, pos, agent.player_id]])
                await agent.client.debug_create_unit([[UnitTypeId.STALKER, 2, pos, agent.player_id]])
            else:
                raise NotImplementedError

            #for these scenarios we set the enemy location to the opposite unit start, this helps them to fight units and not each others hatcheries
            [p for p in self.players if p != agent][0].enemy_location_0 = self.get_pos(agent,1)


        if agent.setup_stage == 3:
            #Wait for created units and structures to spawn
            #Note: require at least 3 units always to progress
            if len(agent.units.filter(lambda u: u.type_id not in [UnitTypeId.LARVA, UnitTypeId.EGG])) >= 3:
                agent.setup_stage = 4

                #repair buildings:
                for u in agent.structures:
                    if u.health < u.health_max:
                        await agent.client.debug_set_unit_value(u, 2, value=u.health_max)

        if agent.setup_stage == 4:
            agent.setup_stage = 5
            # First round of upgrades

        if agent.setup_stage == 5:
            agent.setup_stage = 6
            # Second round of upgrades

        if agent.setup_stage == 6:
            agent.setup_stage = 7
            # Second round of upgrades
            agent.setup_wait = 16


        if agent.setup_stage == 7:
            agent.setup_wait -= 1 # A little bit of a delay to make sure all broodlings spawned so we can delete them again
            if agent.setup_wait > 0:
                return

            agent.setup_stage = 8
            # Third round of upgrades


            #Kill garbage/temp units here to not interfere
            garbage = agent.units.filter(lambda u: u.type_id in [UnitTypeId.BROODLINGESCORT, UnitTypeId.BROODLING, UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.AUTOTURRET, UnitTypeId.INFESTEDTERRAN, UnitTypeId.LOCUSTMPFLYING, UnitTypeId.LOCUSTMP])
            if garbage:
                await agent.client.debug_kill_unit(garbage)

        if agent.setup_stage == 8:
            agent.setup_stage = 100
            # Set unit energy levels

            b = agent.get_brain()
            if b:
                b.used += 1 # brain is being used now!

            #Disable fast build:
            await agent.client.debug_fast_build()

            #Find the "death building":
            for u in agent.structures:
                if u.type_id in [UnitTypeId.GREATERSPIRE, UnitTypeId.FLEETBEACON, UnitTypeId.FUSIONCORE]:
                    agent.death_struct_tag = u.tag
                    break
            assert agent.death_struct_tag > 0

            #determine start wealth:
            m, v = calculate_wealth(agent)
            agent.start_wealth = m + v*1.5
            self.end_time = agent.time + 60.0 # 60 seconds is more than enough time for them to do something
            #print(f"player {agent.player_id} scenario start wealth = {agent.start_wealth}")

            #Maybe give units commands
            #GO!


class Protagonist(sc2.BotAI, TrainableAgent):
    def __init__(self, master, *args):
        super(Protagonist,self).__init__(*args)
        self.master : TrainingMaster = master
        self.brain = AgentBrain()

        self.setup_stage = 0
        self.start_wealth = 1000

        # disable macro and set training mode tactics for now
        self.disable_macro = True
        self.debug = global_debug

        self.death_struct_tag = -1

        self.do_it = True
        self.enemy_location_0 : Point2 = None

    async def on_start(self):
        self.master.register_player(self)
        self.enemy_location_0 = self.game_info.map_center
        await super(Protagonist,self).on_start()


    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.master.step0_setup(self)
            self.do_it = True
            return

        if self.master.setup_in_progress:
            #setup is in progress
            await self.master.setup_scenario(self)
            self.do_it = True
        else:
            if self.do_it:
                self.do_it = True
                u : Unit
                for u in self.units:
                    self.do(u.attack(self.enemy_location_0))

            # Check if scenario ended?
            self.master.check_scenario_end(self)

    async def on_unit_destroyed(self, unit_tag):
        await super(Protagonist, self).on_unit_destroyed(unit_tag)
        if unit_tag == self.death_struct_tag:
            self.death_struct_tag = -1

    #protagonist doesn't have a brain at this stage
    def use_brain(self, brain : AgentBrain):
        pass
    def get_brain(self) -> AgentBrain:
        # Fake brain just to make the trained happy
        return self.brain

#this class can inherit anything but must eventually inherit sc2.BotAI to be a bot
class BotInTraining(MicroAgentC2):
    def __init__(self, master , *args):
        super(BotInTraining,self).__init__(*args)
        self.master : TrainingMaster = master
        self.setup_stage = 0
        self.start_wealth = 1000

        #disable macro and set training mode tactics for now
        self.disable_macro = True
        self.tactic = MicroAgentC2.TACTIC_TRAIN_1
        self.debug = global_debug

        self.death_struct_tag = -1


    async def on_start(self):
        self.master.register_player(self)
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

            #Check if scenario ended?
            self.master.check_scenario_end(self)

    async def on_unit_destroyed(self, unit_tag):
        await super(BotInTraining, self).on_unit_destroyed(unit_tag)
        if unit_tag == self.death_struct_tag:
            self.death_struct_tag = -1





#create training master
random.seed()
np.random.seed()

print("Here we go...")

the_master = TrainingMaster()

#Run training game

#TODO: fix error with flat64 map, apparently expansion at 24.5 / 61.5 is not in the list?

run_game(maps.get("Flat96"), [
    Bot(Race.Zerg, BotInTraining(the_master)),
    Bot(Race.Zerg, Protagonist(the_master)),
], realtime=global_debug)