"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from enum import Enum

class MessageType(Enum):
    SYNC = 'SYNC'
    VALUE = 'VALUE'
    NOTIFY = 'NOTIFY'
