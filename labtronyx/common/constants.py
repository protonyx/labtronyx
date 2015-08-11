"""
Constants used by the Labtronyx framework
"""

from enum import Enum

class ManagerEvents(Enum):

    shutdown = "MANAGER_SHUTDOWN"

class ResourceEvents(Enum):

    created = "RESOURCE_CREATED"

    destroyed = "RESOURCE_DESTROYED"

    status_changed = "RESOURCE_STATUS"

    driver_load = "DRIVER_LOADED"

    driver_unload = "DRIVER_UNLOADED"

class ResourceStatus(Enum):

    initialize = -1
    ready = 100
    error = 101