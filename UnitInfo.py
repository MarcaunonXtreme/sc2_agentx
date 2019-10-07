


from sc2.constants import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from BaseAgentA1 import BaseAgentA1

#This file helps with various upgrade tracking and so forth
from sc2.game_data import UnitTypeData

import numpy as np

# Base class for unit info tracking
class UnitInfoBase:
    def __init__(self, agent : BaseAgentA1, type_id : UnitTypeId, upgrade_ ):
        self.agent = agent 
        self.type_id = type_id
        self.upgrades = upgrade_list

        self._type_data : UnitTypeData = agent._game_data.units[type_id.value]
        assert isinstance(self._type_data, UnitTypeData)


    @property
    def type_data(self) -> UnitTypeData:
        return self._type_data

    @property
    def name(self) -> str:
        """ Returns the name of the unit. """
        return self._type_data.name

    @property
    def race(self) -> Race:
        """ Returns the race of the unit """
        return Race(self._type_data._proto.race)

    @property
    def is_structure(self) -> bool:
        """ Checks if the unit is a structure. """
        return IS_STRUCTURE in self._type_data.attributes

    @property
    def is_light(self) -> bool:
        """ Checks if the unit has the 'light' attribute. """
        return IS_LIGHT in self._type_data.attributes

    @property
    def is_armored(self) -> bool:
        """ Checks if the unit has the 'armored' attribute. """
        return IS_ARMORED in self._type_data.attributes

    @property
    def is_biological(self) -> bool:
        """ Checks if the unit has the 'biological' attribute. """
        return IS_BIOLOGICAL in self._type_data.attributes

    @property
    def is_mechanical(self) -> bool:
        """ Checks if the unit has the 'mechanical' attribute. """
        return IS_MECHANICAL in self._type_data.attributes

    @property
    def is_massive(self) -> bool:
        """ Checks if the unit has the 'massive' attribute. """
        return IS_MASSIVE in self._type_data.attributes

    @property
    def is_psionic(self) -> bool:
        """ Checks if the unit has the 'psionic' attribute. """
        return IS_PSIONIC in self._type_data.attributes


    @property
    def tech_alias(self) -> Optional[List[UnitTypeId]]:
        """ Building tech equality, e.g. OrbitalCommand is the same as CommandCenter
        For Hive, this returns [UnitTypeId.Hatchery, UnitTypeId.Lair]
        For SCV, this returns None """
        return self._type_data.tech_alias

    @property
    def unit_alias(self) -> Optional[UnitTypeId]:
        """ Building type equality, e.g. FlyingOrbitalCommand is the same as OrbitalCommand
        For flying OrbitalCommand, this returns UnitTypeId.OrbitalCommand
        For SCV, this returns None """
        return self._type_data.unit_alias

    @property_immutable_cache
    def _weapons(self):
        """ Returns the weapons of the unit. """
        try:
            return self._type_data._proto.weapons
        except:
            return None

    @property_immutable_cache
    def can_attack(self) -> bool:
        """ Checks if the unit can attack at all. """
        # TODO BATTLECRUISER doesnt have weapons in proto?!
        return bool(self._weapons) or self.type_id in {UNIT_BATTLECRUISER, UNIT_ORACLE}

    @property_immutable_cache
    def can_attack_both(self) -> bool:
        """ Checks if the unit can attack both ground and air units. """
        if self.type_id == UNIT_BATTLECRUISER:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_BOTH for weapon in self._weapons)
        return False

    @property_immutable_cache
    def can_attack_ground(self) -> bool:
        """ Checks if the unit can attack ground units. """
        if self.type_id in {UNIT_BATTLECRUISER, UNIT_ORACLE}:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_GROUND for weapon in self._weapons)
        return False


    @property_immutable_cache
    def _ground_range(self) -> Union[int, float]:
        """ Returns the range against ground units. Does not include upgrades. """
        if self.type_id == UNIT_ORACLE:
            return 4
        if self.type_id == UNIT_BATTLECRUISER:
            return 6
        if self.can_attack_ground:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_GROUND), None)
            if weapon:
                return weapon.range
        return 0

    def get_ground_attack_range(self):
        return self._ground_range


    @property_immutable_cache
    def _ground_attack_speed(self) -> Union[int, float]:
        """ Returns the dps against ground units. Does not include upgrades. """
        if self.can_attack_ground:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_GROUND), None)
            if weapon:
                return weapon.speed
        return 1.0

    @property_immutable_cache
    def _air_attack_speed(self) -> Union[int, float]:
        """ Returns the dps against air units. Does not include upgrades. """
        if self.can_attack_air:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_AIR), None)
            if weapon:
                return weapon.speed
        return 1.0

    def get_ground_attack_speed(self):
        return self._ground_attack_speed

    def get_air_attack_speed(self):
        return self._air_attack_speed

    @property_immutable_cache
    def can_attack_air(self) -> bool:
        """ Checks if the unit can air attack at all. Does not include upgrades. """
        if self.type_id == UNIT_BATTLECRUISER:
            return True
        if self._weapons:
            return any(weapon.type in TARGET_AIR for weapon in self._weapons)
        return False

    @property_immutable_cache
    def _air_range(self) -> Union[int, float]:
        """ Returns the range against air units. Does not include upgrades. """
        if self.type_id == UNIT_BATTLECRUISER:
            return 6
        if self.can_attack_air:
            weapon = next((weapon for weapon in self._weapons if weapon.type in TARGET_AIR), None)
            if weapon:
                return weapon.range
        return 0

    def get_air_attack_range(self):
        return self._air_range

    @property
    def armor(self) -> Union[int, float]:
        """ Returns the armor of the unit. Does not include upgrades """
        return self._type_data._proto.armor

    @property
    def sight_range(self) -> Union[int, float]:
        """ Returns the sight range of the unit. """
        return self._type_data._proto.sight_range

    @property
    def _movement_speed(self) -> Union[int, float]:
        """ Returns the movement speed of the unit. Does not include upgrades or buffs. """
        return self._type_data._proto.movement_speed

    @property
    def is_mineral_field(self) -> bool:
        """ Checks if the unit is a mineral field. """
        return self._type_data.has_minerals

    @property
    def is_vespene_geyser(self) -> bool:
        """ Checks if the unit is a non-empty vespene geyser or gas extraction building. """
        return self._type_data.has_vespene

    @property
    def cargo_size(self) -> Union[float, int]:
        """ Returns the amount of cargo space the unit needs. """
        return self._type_data.cargo_size

    def get_movement_speed(self):
        return self._movement_speed

    def get_base_armor(self):
        return self.armor 




class UnitInfo_Zergling(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.ZERGLINGMOVEMENTSPEED]:
            return self._movement_speed*1.6
        else
            return self._movement_speed

    def get_ground_attack_speed(self):
        if self.upgrade[UpgradeId.ZERGLINGATTACKSPEED]:
            return self._ground_attack_speed-0.15 
        else:    
            return self._ground_attack_speed


class UnitInfo_Baneling(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.CENTRIFICALHOOKS]:
            return self._movement_speed*1.18
        else
            return self._movement_speed

class UnitInfo_Roach(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.GLIALRECONSTITUTION]:
            return self._movement_speed*1.33
        else:
            return self._movement_speed


class UnitInfo_Hydra(UnitInfoBase):
    def get_movement_speed(self):
        if self.upgrades[UpgradeId.EVOLVEMUSCULARAUGMENTS]:
            return self._movement_speed*1.25
        else:
            return self._movement_speed

    def get_ground_attack_range(self):
        if self.upgrades[UpgradeId.EVOLVEGROOVEDSPINES]:
            return self._ground_range + 1
        else:
            return self._ground_range

    def get_air_attack_range(self):
        if self.upgrades[UpgradeId.EVOLVEGROOVEDSPINES]:
            return self._ground_range + 1
        else:
            return self._ground_range


class UnitInfo_Ultralist(self):

    def get_movement_speed(self):
        if self.upgrades[UpgradeId.ANABOLICSYNTHESIS]:
            return self._movement_speed*1.2
        else:
            return self._movement_speed

    def get_base_armor(self):
        if self.upgrades[UpgradeId.CHITINOUSPLATING]:
            return 4
        else:
            return 2



UNIT_INFO_LIST = {

}




def get_unit_info(agent : BaseAgentA1, type_id : UnitTypeId) -> UnitInfoBase:
    tmp = UNIT_INFO_LIST.get(type_id, None)
    if not tmp:
        tmp = UnitInfoBase(agent, type_id)
        UNIT_INFO_LIST[type_id] = tmp
    return tmp












