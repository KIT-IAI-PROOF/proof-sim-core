"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from __future__ import annotations

from enum import Enum


class BlockStatus(Enum):
    UNKNOWN = 'UNKNOWN'
    CREATED = 'CREATED'
    INITIALIZED = 'INITIALIZED'
    WAITING = 'WAITING'
    READY = 'READY'
    EXECUTION_STEP_FINISHED = 'EXECUTION_STEP_FINISHED'
    EXECUTION_FINISHED = 'EXECUTION_FINISHED'
    FINALIZED = 'FINALIZED'
    STOPPED = 'STOPPED'
    SHUT_DOWN = 'SHUT_DOWN'
    ERROR_INIT = 'ERROR_INIT'
    ERROR_STEP = 'ERROR_STEP'
    ERROR_FINALIZE = 'ERROR_FINALIZE'

