from logic.singleton import Singleton


class FileService(metaclass=Singleton):

    def __init__(self):
        self.files = []
