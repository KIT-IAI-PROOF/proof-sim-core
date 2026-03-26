"""
This module contains an exemplary for testing the methods of default core.
"""
import argparse
import json
import os
import unittest

from proofcore.base.basewrapper import value_function, sync_function
from proofcore.core.fmuwrapper import FmuWrapper
from proofcore.models.data import ValueMessage, TactMessage

path = os.path.dirname(__file__)
with open(os.path.join(path, 'inputs/inputList.json')) as f:
    inputs = json.loads(f.read())
with open(os.path.join(path, 'inputs/outputsList.json')) as f:
    outputs = json.loads(f.read())
with open(os.path.join(path, 'inputs/messageValue.json')) as f:
    input_message_value = json.loads(f.read())
with open(os.path.join(path, 'inputs/messageTact.json')) as f:
    input_message_tact_list = json.loads(f.read())
with open(os.path.join(path, 'outputs/messageValue.json')) as f:
    output_value_list = json.loads(f.read())
with open(os.path.join(path, 'outputs/messageNotify.json')) as f:
    output_notify_list = json.loads(f.read())

p = argparse.ArgumentParser()
p.add_argument('--name', '-n', dest='name', default="model")
p.add_argument('--directory', '-w', dest='directory', default=path)
p.add_argument('--file', '-f', dest='file', default=os.path.join(path, 'inputs/rectifier.fmu'))
p.add_argument('--inputs', '-i', dest='inputs', default=json.dumps(inputs))
p.add_argument('--outputs', '-o', dest='outputs', default=json.dumps(outputs))
options, arguments = p.parse_known_args()


class TestFmuWrapper(unittest.TestCase):

    def setUp(self):
        self.model = FmuWrapper(opt=options)
        values = {}
        for key in self.model.outputs:
            values[key["name"]] = "data"
        self.model.set_variables(values)

    def test_set_variables(self):
        """
        Function tests if message_value["data"] was correctly set by setVariables function.
        """
        message = ValueMessage(**input_message_value)
        self.model.set_variables(message.data)
        output = input_message_value["data"]
        for key in output:
            output[key] = getattr(self.model, key)
        self.assertEqual(output, input_message_value["data"])  # add assertion here

    def test_value_message(self):
        """
        tests valueFunction() method
        """
        value_function(message=ValueMessage(**input_message_value), model=self.model)

    def test_tact_message(self):
        """
        tests tactFunction() method
        """
        sync_function(message=TactMessage(**input_message_tact_list[0]), model=self.model)
        sync_function(message=TactMessage(**input_message_tact_list[1]), model=self.model)
        sync_function(message=TactMessage(**input_message_tact_list[2]), model=self.model)


if __name__ == '__main__':
    unittest.main()
