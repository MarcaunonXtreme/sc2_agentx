
import sc2
from sc2 import run_game, maps, Race #, Difficulty
from sc2.player import Bot #, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.game_data import  UnitTypeData
from sc2.position import Point2

from sc2.dicts.unit_tech_alias import UNIT_TECH_ALIAS

from sc2.constants import UnitTypeId

from AgentBrain import AgentBrain
from TrainableAgent import TrainableAgent

from MicroAgentC2 import MicroAgentC2

from scenarios import *

from copy import deepcopy
import random
import numpy as np

from Protagonist1 import Protagonist

global_debug = True

###Scenario control:
## Ultimately we want to play every scenario at least 6 times (for genetic algorithms)
## twice with the agents swapped in both directions
## Then three times do that with different pairs of agents
## At the end of every scenario:
##

def get_type_id(unit : Unit):
    s = UNIT_TECH_ALIAS.get(unit.type_id,None)
    if s:
        return next(iter(s))
    else:
        return unit.type_id


class XMem:
    def __init__(self, type_id, position = None):
        self.type_id : UnitTypeId = type_id
        self.position : Point2 = position
        self.tag = 0
        self.amount = 0

class TrainingData:
    def __init__(self, agent):
        self.agent = agent
        self.xmem = [] # this is for structures
        self.units = [] # also xmem but for scenario units
        self.position : Point2 = Point2()
        self.natural_expansion = random.random() > 0.5


class TrainingMaster:
    def __init__(self, nr_brains = 30):
        self.players = [None, None]
        self.players_data = [None, None]


        self.round = 0
        self.end_time = 90.0

        self.got_positions = False
        self.position = [Point2(),Point2()]
        self.battle_field_position : Point2 = Point2()

        self.brains = []
        for nr in range(nr_brains):
            self.brains.append(AgentBrain.load(f"agents/agent_{nr}.p"))


    def register_player(self, bot : (TrainableAgent, sc2.BotAI)):
        bot.training_data = TrainingData(bot)

        if bot.player_id == 1:
            print("Player 1 registered")
            self.players[0] = bot
            self.players_data[0] = bot.training_data
        else:
            assert bot.player_id == 2
            print("Player 2 registered")
            self.players[1] = bot
            self.players_data[1] = bot.training_data


    @property
    def setup_in_progress(self):
        return self.players[0].setup_stage < 10 or self.players[1].setup_stage < 10


    def setup_scenario_units(self):

        keys = list(SCENARIOS1.keys())
        amount = len(keys)
        key = keys[random.randint(0,amount-1)]
        scenario = SCENARIOS1[key]

        for p in range(2):
            data :TrainingData = self.players_data[p]

            index = RACE_INDEX[self.players[p].race]

            unit_list : list = scenario[index]

            for units in unit_list:
                tmp = XMem(units[0])
                tmp.amount = random.randint(units[1],units[2])
                data.units.append(tmp)



    async def step0_setup(self, agent : (TrainableAgent, sc2.BotAI)):
        print("Step 0 setup...")
        # firstly remove all existing units :)
        await agent.client.debug_kill_unit(agent.units)
        #TODO: fix up starting positions so scouting isn't necessary
        #TODO: on 4-player maps fix this so that the bases gets moved to the corner locations


        data : TrainingData = agent.training_data

        u :Unit
        for u in agent.structures:
            tmp = XMem(u.type_id,u.position)
            tmp.tag = u.tag
            data.xmem.append(tmp)

        # add 1 gas building:
        main_base = agent.expansion_locations[agent.start_location]
        # print("====")
        # print(main_base)
        main_base: Units = Units(main_base, agent)

        #Note: not sure this is really workable?
        if agent.race == Race.Zerg:

            #add pool:
            loc = await agent.find_placement(UnitTypeId.SPAWNINGPOOL, agent.start_location.towards(agent.game_info.map_center,5))
            assert loc
            pool = XMem(UnitTypeId.SPAWNINGPOOL, loc)
            data.xmem.append(pool)

            gas = XMem(UnitTypeId.EXTRACTOR, main_base.vespene_geyser[0].position)
            data.xmem.append(gas)

            #Spread some creep towards the ramp at least
            loc : Point2 = agent.start_location.towards(agent.main_base_ramp.top_center, 10)
            creep = XMem(UnitTypeId.CREEPTUMORBURROWED, loc)
            data.xmem.append(creep)

            #TODO: spore in main mineral line?
            #TODO: defense spine crawler?
            #TODO: add a few overlords to be realistic (but they aren't structures!??)

            if data.natural_expansion:
                loc = await agent.get_next_expansion()
                assert loc
                data.xmem.append(XMem(UnitTypeId.HATCHERY, loc))

                #TODO: wall?
                #TODO: defense spines?


        elif agent.race == Race.Terran:

            #build a rax and 2 depots on the ramp:
            data.xmem.append(XMem(UnitTypeId.BARRACKS, agent.main_base_ramp.barracks_in_middle))
            for loc in agent.main_base_ramp.corner_depots:
                data.xmem.append(XMem(UnitTypeId.SUPPLYDEPOT, loc))

            gas = XMem(UnitTypeId.REFINERY, main_base.vespene_geyser[0].position)
            data.xmem.append(gas)

            if data.natural_expansion:
                loc = await agent.get_next_expansion()
                assert loc
                data.xmem.append(XMem(UnitTypeId.ORBITALCOMMAND, loc))

                #TODO: Natural wall?

                #Add a defense bunker in front of natural 50% chance
                if random.random() > 0.5:
                    loc = loc.towards(agent.game_info.map_center, 10)
                    loc = await agent.find_placement(UnitTypeId.BUNKER, loc)
                    assert loc
                    data.xmem.append(XMem(UnitTypeId.BUNKER, loc))



        elif agent.race == Race.Protoss:

            #Build a gatway and pylon and core around the ramp
            data.xmem.append(XMem(UnitTypeId.PYLON, agent.main_base_ramp.protoss_wall_pylon))
            for unit,pos in zip({UnitTypeId.GATEWAY, UnitTypeId.CYBERNETICSCORE}, agent.main_base_ramp.protoss_wall_buildings):
                data.xmem.append(XMem(unit, pos))

            gas = XMem(UnitTypeId.ASSIMILATOR, main_base.vespene_geyser[0].position)
            data.xmem.append(gas)

            #TODO: more pylons
            #TODO: cannon in mineral line(s)


            if data.natural_expansion:
                exp_loc = await agent.get_next_expansion()
                assert exp_loc
                data.xmem.append(XMem(UnitTypeId.NEXUS, exp_loc))

                loc2 = exp_loc.towards(agent.game_info.map_center, 3)
                loc = await agent.find_placement(UnitTypeId.PYLON, loc2)
                if loc:
                    data.xmem.append(XMem(UnitTypeId.PYLON, loc))

                #TODO: an actual wall?

                #if random.random() > 0.3:
                #    loc2 = exp_loc.towards(agent.game_info.map_center, 4)
                #    loc = await agent.find_placement(UnitTypeId.SHIELDBATTERY, loc2)
                #    assert loc
                #    data.xmem.append(XMem(UnitTypeId.SHIELDBATTERY, loc))

                if random.random() > 0.6:
                    loc2 = exp_loc.towards(agent.game_info.map_center, 5)
                    loc = await agent.find_placement(UnitTypeId.PHOTONCANNON, loc2)
                    if loc:
                        data.xmem.append(XMem(UnitTypeId.PHOTONCANNON, loc))


        else:
            raise NotImplementedError

        #Upgrade levels:
        upgrade_level = random.randint(0,3)
        print(f"Upgrade Level for agent = {upgrade_level}")
        for i in range(upgrade_level):
            await agent.client.debug_upgrade()

    async def repair_setup(self, agent: (TrainableAgent, sc2.BotAI)):

        data: TrainingData = agent.training_data
        s : XMem
        for s in data.xmem:
            unit : Unit = None if s.tag == 0 else agent.structures.find_by_tag(s.tag)
            if not unit:

                if s.type_id in [UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORQUEEN]:
                    #find it:
                    all_tumors = agent.structures.filter(lambda u: u.type_id in [UnitTypeId.CREEPTUMORBURROWED, UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORQUEEN])
                    if all_tumors:
                        unit = all_tumors.closest_to(s.position)
                        if unit.distance_to(s.position) < 4.0:
                            s.tag = unit.tag
                        else:
                            unit = None
                else:
                    # Maybe the building already exist?
                    all_of_type = agent.structures.filter(lambda u: get_type_id(u) == s.type_id or u.type_id == s.type_id)
                    if all_of_type:
                        unit = all_of_type.closest_to(s.position)
                        if (get_type_id(unit) == s.type_id or unit.type_id == s.type_id)  and unit.distance_to(s.position) < 5.0:
                            s.tag = unit.tag
                        else:
                            unit = None

            if unit:
                #magically repair existing building
                await agent.client.debug_set_unit_value(unit, 1, value=unit.energy_max)
                await agent.client.debug_set_unit_value(unit, 2, value=unit.health_max)
                await agent.client.debug_set_unit_value(unit, 3, value=unit.shield_max)
            else:
                #Doesn't exist anymore, create a new one
                s.tag = 0
                #will have to find the unit later!
                print(f"Creating {s.type_id} -> {s.position}")
                await agent.client.debug_create_unit([[s.type_id, 1, s.position, agent.player_id]])



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


    def end_scenario_now(self, bonus_time):
        print("=SCENARIO ENDED=")
        end_time = self.players[0].time
        print(f"Scenario ended in {end_time}")
        lost_wealth = []
        for agent in self.players:
            agent.setup_stage = 0
            m, v = agent.calculate_wealth(agent)
            wealth = m + v * 1.5
            #print(f"Player {agent.player_id} end wealth = {wealth}")
            lost_wealth.append(abs(wealth - agent.start_wealth))

        #TODO: adjust also based on time taken
        #TODO: adjust for partial damage?? (not sure this is a good idea?)
        p1_score = lost_wealth[1] - lost_wealth[0]
        #p2_score = lost_wealth[0] - lost_wealth[1]
        if p1_score > 0:
            #in case we did okay or good the faster we won the better!
            if bonus_time > 0:
                p1_score += round(bonus_time)
        elif p1_score < 0:
            #if we lost, the longer we kept enemy busy the better (slightly)
            #ie the faster the enemy killed us the worst it is
            if bonus_time > 0:
                p1_score -= round(bonus_time)

        p1_score += lost_wealth[1] * 0.1 # 10% of enemy losses are directly added as score - then encourage engagement rather than running away

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

        if agent.time >= self.end_time:
            print("Scenario ended due to time limit")
            self.end_scenario_now( self.end_time - agent.time  )
        if len(agent.structures) <= 2:
            print("Agent lost too many buildings!")
            self.end_scenario_now(self.end_time - agent.time)
        elif len(agent.units) < 16:
            #See if combat units are all gone?
            cnt = agent.units.filter(lambda u: u.type_id not in [UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.BROODLING, UnitTypeId.CREEPTUMOR, UnitTypeId.CREEPTUMORBURROWED])
            if len(cnt) <= 0:
                print("Units lost, ending scenario")
                self.end_scenario_now( self.end_time - agent.time )



    def calculation_positions(self):

        #TODO: majorly improve this crap

        centre: Point2 = self.players[0].game_info.map_center

        self.position[0] = centre.towards(self.players[0].start_location, 15)

        self.position[1] = centre.towards(self.players[1].start_location, 15)

        for i in range(2):
            pos = self.position[i]
            self.position[i] = pos.rounded
            self.players_data[i].position = pos.rounded

        self.battle_field_position = centre.rounded
        self.got_positions = True

    async def create_scenario_units(self, agent, data):
        pos: Point2 = data.position.rounded

        print("Creating units...")
        x : XMem
        for x in data.units:
            await agent.client.debug_create_unit([[x.type_id, x.amount, pos, agent.player_id]])


    async def setup_scenario(self, agent : (TrainableAgent, sc2.BotAI)):
        assert isinstance(agent, TrainableAgent)
        assert isinstance(agent, sc2.BotAI)
        assert isinstance(self.players_data[0], TrainingData)
        assert isinstance(self.players_data[1], TrainingData)
        #print(f"Player {agent.player_id} setup stage = {agent.setup_stage}")
        if not self.got_positions:
            self.calculation_positions()
            self.setup_scenario_units()

        data : TrainingData = agent.training_data

        if agent.setup_stage == 0:
            #load checkpoint:
            if agent.player_id == 1:
                print("== STARTING NEW SCENARIO ==")


            if not isinstance(agent, Protagonist):
                # Non Protagonist gets brain :)
                chosen = None
                for b in self.brains:
                    if b.used == 0:
                        chosen = b
                        break
                assert chosen
                agent.use_brain(chosen)


            await agent.client.debug_fast_build()
            # clear old units:
            if agent.units:
                await agent.client.debug_kill_unit(agent.units)

            agent.setup_stage = 1

        if agent.setup_stage == 1:

            # Wait for all old units to be removed
            if len(agent.units.filter(lambda u: u.type_id not in [UnitTypeId.LARVA, UnitTypeId.EGG])) == 0:
                agent.setup_stage = 2

        if agent.setup_stage == 2:

            #repair buildings
            await self.repair_setup(agent)
            agent.setup_stage = 3

        if agent.setup_stage == 3:

            await self.create_scenario_units(agent,data)

            #set target location
            agent.enemy_location_0 = self.battle_field_position
            agent.setup_stage = 4

        if agent.setup_stage == 4:
            #Wait for created units and structures to spawn
            #Note: require at least 3 units always to progress
            if len(agent.units.filter(lambda u: u.type_id not in [UnitTypeId.LARVA, UnitTypeId.EGG])) >= 3:
                agent.setup_stage = 5

        if agent.setup_stage == 5:
            agent.setup_stage = 6


        if agent.setup_stage == 6:
            agent.setup_stage = 7

            agent.setup_wait = 11

        if agent.setup_stage == 7:
            agent.setup_wait -= 1 # A little bit of a delay to make sure all broodlings spawned so we can delete them again
            if agent.setup_wait > 0:
                return



            #Kill garbage/temp units here to not interfere
            garbage = agent.units.filter(lambda u: u.type_id in [UnitTypeId.BROODLINGESCORT, UnitTypeId.BROODLING, UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.MULE, UnitTypeId.AUTOTURRET, UnitTypeId.INFESTEDTERRAN, UnitTypeId.LOCUSTMPFLYING, UnitTypeId.LOCUSTMP])
            if garbage:
                await agent.client.debug_kill_unit(garbage)

            agent.setup_stage = 8
            # Third round of upgrades

        if agent.setup_stage == 8:
            # Final stage

            # Set unit energy levels

            #activate brain:
            b = agent.get_brain()
            if b:
                b.used += 1 # brain is being used now!

            #Disable fast build:
            await agent.client.debug_fast_build()

            #determine start wealth:
            m, v = agent.calculate_wealth()
            agent.start_wealth = m + v*1.5
            self.end_time = agent.time + 60.0 # 60 seconds is more than enough time
            #print(f"player {agent.player_id} scenario start wealth = {agent.start_wealth}")

            #Maybe give units commands
            #GO!
            agent.setup_stage = 100



#TODO: move to other file?
#this class can inherit anything but must eventually inherit sc2.BotAI to be a bot
class BotInTraining(MicroAgentC2, TrainableAgent):
    def __init__(self, master , *args):
        MicroAgentC2.__init__(self, *args)
        TrainableAgent.__init__(self)
        self.master : TrainingMaster = master

        #disable macro and set training mode tactics for now
        self.disable_macro = True
        self.disable_strategy = True
        self.tactic = MicroAgentC2.TACTIC_TRAIN_1 #TODO: fix this
        self.debug = global_debug


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
        #if unit_tag == self.death_struct_tag:
        #    self.death_struct_tag = -1

    async def on_building_construction_complete(self, unit: Unit):
        print("New building popped up!!")
        await super(BotInTraining, self).on_building_construction_complete(unit)



#create training master
random.seed()
np.random.seed()

print("Here we go...")

the_master = TrainingMaster()

#Run training game

#TODO: fix error with flat64 map, apparently expansion at 24.5 / 61.5 is not in the list?


map_names = [
    "AcropolisLE",
    "DiscoBloodbathLE",
    "EphemeronLE",
    "ThunderbirdLE",
    "TritonLE",
    "WintersGateLE",
    "WorldOfSleepersLE"
]
map_name = random.choice(map_names)
print(f"Loading map = {map_name}")

run_game(maps.get(map_name), [
    Bot(Race.Random, Protagonist(the_master)),
    Bot(Race.Random, Protagonist(the_master)),
], realtime=global_debug)