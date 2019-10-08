
# Various things to help with upgrades

from sc2.constants import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.game_data import UnitTypeData, UpgradeData
from sc2 import BotAI
from sc2 import Race
import numpy as np

from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM



UPGRADE_MINIMUM_TIMING = np.zeros(312)




def calculate_upgrade_timings(agent: BotAI):

    for upgrade,from_structure in UPGRADE_RESEARCHED_FROM.items():
        upgradeData : UpgradeData = agent.game_data.upgrades[upgrade.value]
        research_time = upgradeData.cost.time #how long this research would take

        #building chain timing calculation
        while from_structure:
            typeData : UnitTypeData = agent.game_data.units[from_structure.value]
            # add time of building if it's not the starting building
            if from_structure not in [UnitTypeId.COMMANDCENTER, UnitTypeId.HATCHERY, UnitTypeId.NEXUS]:
                research_time += typeData.cost.time
            research_time += 2.0
            last_time = typeData.cost.time
            from_structure = typeData.tech_requirement
        
        #add some initial time because it's not like the player can actually start doing any of this immediately.
        research_time += 30.0 # not sure what is a good number? - how long does it take to setup first buildings and gas? etc?

        UPGRADE_MINIMUM_TIMING[upgrade.value] = research_time


