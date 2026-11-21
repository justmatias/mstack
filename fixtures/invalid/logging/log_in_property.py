import logging

logger = logging.getLogger(__name__)


class Item:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        logger.debug("Reading the name")
        return self._name
