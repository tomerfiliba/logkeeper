import unittest
from scrolls import Logger


class SimpleTest(unittest.TestCase):
    def test(self):
        logger = Logger("mylogger")
        logger.info("hello")
        logger.warning("world")
        logger.error("spam")
        with logger.section("working on module 7"):
            logger.info("hello")
            logger.info("world")


if __name__ == "__main__":
    unittest.main()


