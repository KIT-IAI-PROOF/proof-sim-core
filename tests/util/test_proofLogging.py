import unittest
from proofcore.util.proofLogging import Logger, logging  # replace with actual module name

all_levels = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)

class LoggerTest(unittest.TestCase):
    def setUp(self):  # BaseWrapper class is instantiated
        print("Testing Logger")

    def test_logger_creation(self):
        logger_name = 'TestLogger'
        logger = Logger(logger_name).get_logger()

        self.assertIsNotNone(logger)  # logger should not be None
        self.assertEqual(logger_name, logger.name)  # logger should have the correct name

        # Expected values for (Debug, Info, Warning, Error, Critical):
        expected_values = {
            "INFO": (0, 1, 1, 1, 1),
            "DEBUG": (1, 1, 1, 1, 1),
            "ERROR": (0, 0, 0, 1, 1),
        }

        for level in ["INFO", "DEBUG", "ERROR"]:
            logger = Logger('MyLogger', log_level = level).get_logger()
            #logger = Logger('MyLogger').get_logger()
            effective_level = logger.getEffectiveLevel()
            print(f"== Logging test for level '{str(level)}': effective: {effective_level} ")
            log_enabled = [ logger.isEnabledFor(lvl) for lvl in all_levels ]
            diffs = [(i, x, y) for i, (x, y) in enumerate(zip(log_enabled, expected_values[level])) if x != y]
            for diff in diffs:
                print(f"Enable status for {logging._levelToName[all_levels[diff[0]]]} is incorrect: expected: {bool(diff[2])}, status: {diff[1]}") 
            logger.debug('This is a debug message')
            logger.info('This is an info message')
            logger.warning('This is a warning message')
            logger.error('This is an error message')
            logger.critical('This is a critical message')
            print("==")

if __name__ == "__main__":
    unittest.main()