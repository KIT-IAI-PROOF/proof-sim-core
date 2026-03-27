"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from enum import Enum


class SimulationPhase(Enum):
    CREATE = "CREATE"
    INIT = "INIT"
    EXECUTE = "EXECUTE"
    FINALIZE = "FINALIZE"
    SHUTDOWN = "SHUTDOWN"
