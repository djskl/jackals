
class Const(type):
    warning = 'This class is immutable.'
    def __setattr__(self, k, v):
        raise AttributeError(self.warning)

TaskStatus = Const("TaskStatus", (), {
    "SUCCESS": 0,
    "FAILED": -1,
    "CREATE_ERR": -2,
    "RUNING": 1,
    "PENDING": 2,
    "STARTED": 3,
    "KILLED": 4                                      
})
