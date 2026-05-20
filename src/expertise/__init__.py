"""Expertise — Expert Factory System.

Complete pipeline for expert creation, socratic composition, memory,
registry, derived synthesis, and recall. Integrates with governance,
snapdna, dtt, and catalog systems.
"""

from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry
from .expert_creator import ExpertCreator
from .socratic_composer import (
    SocraticComposer,
    SocraticOrchestrator,
    SocraticSession,
    SocraticQuestion,
    AgentRole,
    AgentPersona,
    AgentPerspective,
    DialogueRound,
    PlaybookLibrary,
)
from .derived_synthesizer import DerivedSynthesizer
from .expert_recall import ExpertRecall
from .pipeline import ExpertisePipeline
