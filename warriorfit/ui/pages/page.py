from abc import ABC, abstractmethod


class Page(ABC):

    @abstractmethod
    def get_ui(self):
        pass

    @abstractmethod
    def server(self, input, output, session):
        pass