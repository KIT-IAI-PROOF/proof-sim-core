"""
This module contains an exemplary for testing the methods of default core.
"""
import argparse
import json
import os
import unittest

from proofcore.base.basewrapper import value_function, sync_function
#from proofcore.core.defaultwrapper import DefaultWrapper
from proofcore.templates.WrapperTemplate import WrapperTemplate
from proofcore.models.ValueMessage import ValueMessage
from proofcore.models.SyncMessage import SyncMessage
from proofcore.models.SimulationPhase import SimulationPhase

path = os.path.dirname(__file__)
#with open(os.path.join(path, 'inputs/inputList.json')) as f:
#    inputs = json.loads(f.read())
#with open(os.path.join(path, 'inputs/outputsList.json')) as f:
#    outputs = json.loads(f.read())
inputs = ["test_input_1", "test_input_2", "test_input_3"]
outputs = ["test_output_1", "test_output_2", "test_output_3"]

with open(os.path.join(path, 'inputs/messageValue.json')) as f:
    input_message_value = json.loads(f.read())[0]
with open(os.path.join(path, 'inputs/messageTact.json')) as f:
    input_message_tact_list = json.loads(f.read())
with open(os.path.join(path, 'outputs/messageValue.json')) as f:
    output_value_list = json.loads(f.read())
with open(os.path.join(path, 'outputs/messageNotify.json')) as f:
    output_notify_list = json.loads(f.read())

p = argparse.ArgumentParser()
p.add_argument('--name', '-n', dest='name', default="model")
p.add_argument('--directory', '-w', dest='directory', default=path)
p.add_argument('--file', '-f', dest='file')
p.add_argument('--inputs', '-i', dest='inputs', default=json.dumps(inputs))
p.add_argument('--outputs', '-o', dest='outputs', default=json.dumps(outputs))
p.add_argument('--loggingDir', '-d', dest='loggingDir', default="/tmp")  # example: "/tmp"
p.add_argument('--ports', '-P', dest='ports', default='[]')  # socket ports to read and write data from/to worker. Example: "[40000, 50000]" ([readPort,writePort])
p.add_argument('--local_block_id', '-b', dest='local_block_id')  # example: "2"
options, arguments = p.parse_known_args()

test_case = argparse.Namespace(
    workspace_directory="directory",
    inputs="[]",
    outputs="[ ]",
    logLevel="DEBUG", # example#
    loggingDir="/tmp",
    ports="[]",
    local_block_id="1"
)

class TestDefaultWrapper(unittest.TestCase):

    def setUp(self):
        print("Testing DefaultWrapper")
        #self.model = DefaultWrapper(opt=options)
        self.model = WrapperTemplate(opt=test_case)
        values = {}
        for key in self.model.outputs:
            values[key] = "data"
        self.model.set_variables(values, phase=SimulationPhase.INIT)

    def test_set_variables(self):
        """
        Function tests if message_value["data"] was correctly set by setVariables function.
        """
        message = ValueMessage(**input_message_value)
        # Remark (MM): Unsure which simulation phase is best here.
        self.model.set_variables(message.data, phase=SimulationPhase.EXECUTE)
        output = input_message_value["data"]
        for key in output:
            output[key] = getattr(self.model, key)
        self.assertEqual(output, input_message_value["data"])  # add assertion here

    def test_value_message(self):
        """
        tests valueFunction() method
        """
        value_function(message=ValueMessage(**input_message_value), wrapper=self.model)

    def test_tact_message(self):
        """
        tests tactFunction() method
        """
        sync_function(message=SyncMessage(**input_message_tact_list[0]), wrapper=self.model)
        sync_function(message=SyncMessage(**input_message_tact_list[1]), wrapper=self.model)
        sync_function(message=SyncMessage(**input_message_tact_list[2]), wrapper=self.model)


if __name__ == '__main__':
    unittest.main()
