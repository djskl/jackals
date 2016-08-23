
class Const(type):
    warning = 'This class is immutable.'
    def __setattr__(cls, k, v):
        raise AttributeError(cls.warning)

TaskStatus = Const("TaskStatus", (), {
    "SUCCESS": 0,
    "FAILED": -1,
    "CREATE_ERR": -2,
    "RUNING": 1,
    "SUBMITED": 2,
    "STARTED": 3,
    "KILLED": 4                                      
})
