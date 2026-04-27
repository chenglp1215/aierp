from typing import Dict, List, Optional, Any
from .base import BaseSkill, SkillContext, SkillResult


class SkillRegistry:
    _instance = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill) -> None:
        if not skill.name:
            raise ValueError("Skill name cannot be empty")
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        if name in self._skills:
            del self._skills[name]

    def get(self, name: str) -> Optional[BaseSkill]:
        return self._skills.get(name)

    def get_all(self) -> List[BaseSkill]:
        return list(self._skills.values())

    def get_enabled(self) -> List[BaseSkill]:
        return [s for s in self._skills.values() if s.enabled]

    def get_by_keyword(self, message: str) -> List[BaseSkill]:
        return [s for s in self.get_enabled() if s.should_activate(message)]

    def get_skills(self, skill_ids: List[str]) -> List[BaseSkill]:
        return [s for s in self._skills.values() if s.name in skill_ids]
    
    def has(self, name: str) -> bool:
        return name in self._skills

    def clear(self) -> None:
        self._skills.clear()


skill_registry = SkillRegistry()
