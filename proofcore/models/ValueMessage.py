"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
from typing import Any, Optional
from pydantic import Field
from proofcore.models.BaseMessage import BaseMessage

"""
A class transporting values from the worker (Java) to the wrapper (Python) and vice versa
Most functions are derived from base class 'BaseMessage'
"""
class ValueMessage(BaseMessage):
    data: Optional[Any] = Field(
        None, description='Payload of the message. Contains the data.'
    )
