
class Const(type):
    warning = 'This class is immutable.'
    def __setattr__(self, k, v):
        raise AttributeError(self.warning)
    
    def toList(self):
        status = [(name, value) for name, value in self.__dict__.items() if not name.startswith('__')]
        return status
    
    def toDict(self):
        status = {name: value for name, value in self.__dict__.items() if not name.startswith('__')}
        return status
        
TaskStatus = Const("TaskStatus", (), {
    "SUCCESS": 0,
    "PENDING": 1,
    "RUNING": 2,
    "FAILED": -1,
    "TIMEOUT": -2,
    "KILLED": -3                                     
})
