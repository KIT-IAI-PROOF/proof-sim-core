# This file enables easy debugging of unittests
import unittest
from tests.base.test_basewrapper import TestBaseWrapper
from tests.core.default.test_default_wrapper import TestDefaultWrapper 
from tests.templates.test_wrapper_template import TestDefaultWrapper 
from tests.util.test_proofLogging import LoggerTest

if __name__ == '__main__':
    unittest.main()