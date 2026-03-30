"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from proofcore.models.BaseMessage import BaseMessage
from proofcore.models.BlockStatus import BlockStatus

"""
A class transporting a notification from the wrapper (Python) to the worker (Java)
Most functions are derived from base class 'BaseMessage'
"""
class NotifyMessage(BaseMessage):
    status: Optional[BlockStatus] = Field(
        default=BlockStatus.WAITING, description='The changed status of the block.'
    )
    errorText: Optional[str] = Field(
        default="", description='The error text when an execpiton or error occurred'
    )
