from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from proofcore.models.MessageType import MessageType
from proofcore.models.SimulationPhase import SimulationPhase

"""
this class is based on the Java class BaseMessage (see proof-models)
It is the base class for the three classes NotifyMessage, ValueMessage, and SyncMessage and is used for
the communication between the proof worker (Java) and the wrapper (Python). The messages are sent to a communication
stream (e.g. stdio) as a JSON object and are read from the receiver.

Due to the fact, that the worker reads the JSON messages with gson, which does not deserialize null values, it was decided to
reduce the functionality of the python classes to the necessary and used attributes. This decision avoids the setting of 
inappropriate default values or null values.
"""
class BaseMessage(BaseModel):
    time: Optional[int] = Field(
        None, description='Time that the value message was created.'
    )
    timeInMillis: Optional[int] = Field(
        None, description='Time that the value message was created in milliseconds.'
    )
    type: Optional[MessageType] = Field(
        None,
        description='Type of the Message. Should be either SYNC, VALUE, or NOTIFY'
    )
    communicationPoint: Optional[int] = Field(
        None, description='Tracks the current step'
    )
    globalBlockId: Optional[str] = Field(
        default='unknown', description='UUID of the block this message originates from.'
    )
    localBlockId: Optional[int] = Field(
        default=-1, description='Local id of the block this message originates from.'
    )
    phase: Optional[SimulationPhase] = Field(
        SimulationPhase.INIT, description='the simulation phase for which the message is valid'
    )
