"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from typing import Optional
from proofcore.models.BaseMessage import BaseMessage

from pydantic import Field

"""
A class transporting a synchronize command from the worker (Java) to the wrapper (Python) and vice versa
Most functions are derived from base class 'BaseMessage'
"""
class SyncMessage(BaseMessage):
    communicationStepSize: Optional[int] = Field(
        None, description='Tracks the next (upcoming) stepSize to use'
    )


