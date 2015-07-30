
class Labtronyx_Event(object):

    code = "GENERIC_EVENT"

    def __init__(self, **kwargs):
        self.args = kwargs

    def __str__(self):
        return self.code

class Manager_Shutdown(Labtronyx_Event):
    code = "MANAGER_STOP"

class Resource_Created(Labtronyx_Event):
    code = "RESOURCE_CREATED"

class Resource_Destroyed(Labtronyx_Event):
    code = "RESOURCE_DESTROYED"

class Resource_Status_Changed(Labtronyx_Event):
    code = "RESOURCE_STATUS_CHANGED"
