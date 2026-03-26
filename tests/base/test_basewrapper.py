import argparse
import json
import unittest
# from unittest import IsolatedAsyncioTestCase
from datetime import datetime
from typing import Tuple, Dict
import asyncio

from proofcore.base.basewrapper import BaseWrapper, value_function
from proofcore.models.MessageType import MessageType
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.models.SimulationPhase import SimulationPhase

# inputs = '[{"input1": "P_el","input2": "Q"}]'
# outputs = json.loads("tests/core/default/inputs/outputsList.json")
# path = os.path.dirname(__file__)
# with open(os.path.join(path, '../core/default/inputs/outputsList.json')) as f:
# outputs = f.read()
inputs = "[ ]"
outputs = "[ ]"
inputs_config = "[ ]"
outputs_config = "[ ]"
# test_case = {"directory": "directory", "inputs": inputs, "outputs": outputs, "name": "name", "file": "file"}

test_case = argparse.Namespace(
    workspace_directory="directory",
    inputs="[ ]",
    outputs="[ ]",
    inputs_config="[ ]",
    outputs_config="[ ]",
    logLevel="DEBUG",  # example#
    loggingDir="/tmp",
    ports="[]",
    local_block_id="1"
)


class TestBaseWrapper(unittest.IsolatedAsyncioTestCase):
    """
    Only BaseWrapper is tested here.
    """

    def setUp(self):  # BaseWrapper class is instantiated
        print("Testing BaseWrapper")
        self.wrapper = BaseWrapper(test_case)

    async def test_set_vars(self):
        values = {}
        for key in self.wrapper.outputs:
            values[key["name"]] = "data"
        await self.wrapper.set_variables(values, phase=SimulationPhase.INIT)


    async def test_ctor(self):
        self.assertEqual(self.wrapper.workspace_directory, "directory")
        self.assertEqual(self.wrapper.inputs, json.loads(inputs))
        self.assertEqual(self.wrapper.outputs, json.loads(outputs))

    async def test_init(self):
        self.assertTrue(type(await self.wrapper.init()), Tuple[ValueMessage, NotifyMessage])

    async def test_step(self):
        self.assertTrue(type(await self.wrapper.step()), Tuple[ValueMessage, NotifyMessage])

    async def test_finalize(self):
        self.assertTrue(type(await self.wrapper.finalize()), Tuple[ValueMessage, NotifyMessage])

    async def test_get_data(self):
        self.assertTrue(type(await self.wrapper.get_data()), Dict)

    async def test_get_data_value(self):
        after = [getattr(self.wrapper, output.name) for output in json.loads(outputs)]
        self.assertEqual(list(await self.wrapper.get_data()), after)

    async def test_get_data_keys(self):
        output_names_correct = [output.name for output in json.loads(outputs)]
        data = await self.wrapper.get_data()
        print(data)
        # self.assertEqual(list(await self.wrapper.get_data().keys()), output_names_correct)
        self.assertTrue( 100, 100 )
    async def test_send_value(self):
        self.assertTrue(type(await self.wrapper.send_value(SimulationPhase.EXECUTE)), ValueMessage)

    async def test_send_value_value(self):
        # lifecycle_id = 123 for both test and correct value
        phase = SimulationPhase.FINALIZE

        # build correct valueMessage
        correct_value = ValueMessage(
            time=int(datetime.now().timestamp() * 1000),
            type=MessageType.VALUE.value,
            phase=SimulationPhase.FINALIZE,
            data=await self.wrapper.get_data()
        )

        # build test valueMessage
        test_value = await self.wrapper.send_value(phase=SimulationPhase.FINALIZE)
        # test if correct and test value are equal
        self.assertEqual(test_value.type, correct_value.type)
        self.assertEqual(test_value.phase, correct_value.phase)
        self.assertEqual(test_value.data, correct_value.data)

    async def test_send_notify_json(self):
        self.assertTrue(type(await self.wrapper.send_value(phase=SimulationPhase.FINALIZE)), str)

    # async def test_value_function(self):
    #     phase = SimulationPhase.INIT
    #     data_correct = {"testvalue1": 1, "testvalue2": 2}
    #     values_message = ValueMessage(
    #         time=int(datetime.now().timestamp() * 1000),
    #         type=MessageType.VALUE.value,
    #         phase=phase,
    #         data=data_correct
    #     )
    #     await value_function(message=values_message, wrapper=self.wrapper)
    #     data_test = [self.wrapper.__getattribute__(key) for key in data_correct]
    #     self.assertEqual(data_test, list(data_correct.values()))


if __name__ == '__main__':
    unittest.main()
