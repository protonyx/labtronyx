"""
Getting Started
===============

The typical use case for Labtronyx is as a library that can be imported and used to introduce automation capability
with external instruments. There are many cases, however, where automation with external instruments is the primary
goal of a Python script. For these cases, Labtronyx provides a Script class that handles much of the boiler-plate
operations needed to establish communication with an instrument.

Labtronyx scripts are objects that run commands sequentially from start to completion with an expected outcome. At the
end of a script, a PASS or FAIL designation is returned depending on pre-programmed conditions within the script. Any
class that subclasses the :class:`ScriptBase` class has access to a number of convenience functions to ease interaction
with external instruments or devices through the Labtronyx framework.

To create a Labtronyx script, all you need is a class that extends :class:`ScriptBase` and some code that
instructs the Labtronyx library to run the script::

   import labtronyx
   from labtronyx.script import ScriptBase

   class TestScript(ScriptBase):

       def run(self):
           pass

   if __name__ == '__main__':
       labtronyx.runScriptMain()

To run this simple script, just execute the Python file from the command line.

Script Attributes
-----------------

Attributes provide additional information to Labtronyx about the script that can be used to catalog and identify
scripts in a large repository. It is recommended that scripts define these attributes:

   * author
   * version
   * name
   * description
   * continueOnFail
   * allowedFailures

Declaring Required Resources
----------------------------

Labtronyx is fundamentally an automation framework for instruments. Scripts that subclass :class:`ScriptBase` can
declare required resources by defining class attributes that instantiate the :class:`RequiredResource` class.::

   import labtronyx
   from labtronyx.script import ScriptBase, RequiredResource

   class TestScript(ScriptBase):
       dut = RequiredResource(deviceVendor='Test', deviceModel='Widget')

       def run(self):
           pass

   if __name__ == '__main__':
       labtronyx.runScriptMain()

The parameters for :class:`RequiredResource` are the same parameters passed to `InstrumentManager.FindResources`. These
parameters are used to locate viable resources using the keys returned by the resource method `getProperties`. If the
parameters are not specific enough, it could match more than one resource and cause the script to FAIL because each
required resource must match exactly one resource known to :class:`InstrumentManager`

Running Scripts
---------------

Labtronyx has a helper method that can be used to facilitate script execution from the command line::

   if __name__ == '__main__':
       labtronyx.runScriptMain()

Any file that contains exactly one subclass of :class:`ScriptBase` with that code snippet can be run from the
command line. Alternatively, the script can be instantiated and run by calling the `start` method::

   ts = TestScript()
   result = ts.start()
   print "Script Result: " + result.result

Script Results
--------------

The default outcome or result of a script is a PASS designation. The developer is responsible for deciding when to
return a FAILURE. FAILURES can be set explicitly by calling the `fail` method, or by using on of the convenience
functions to FAIL on a certain condition. If the `continueOnFail` attribute is set, a FAILURE will not stop script
execution, but the outcome of the script will be reported as FAIL. If script execution needs to be stopped on a FAILURE
condition, the `stop` parameter of the `fail` method can be set, or any of the convenience functions beginning with
`assert` will cause execution to halt when the condition is met.
"""
import os
import time
import threading
import ctypes
import logging
from logging.handlers import BufferingHandler

# Package relative imports
from ..common import events
from ..common.errors import *
from ..common.plugin import PluginBase, PluginAttribute, PluginParameter, PluginDependency
from .resource import ResourceBase

__all__ = ['ScriptBase', 'ScriptParameter', 'ScriptResult', 'RequiredResource']


class ScriptBase(PluginBase):
    """
    Script base class, modeled after the Python unittest framework.

    :param manager:         InstrumentManager instance
    :type manager:          labtronyx.InstrumentManager
    :param logger:          Logger instance
    :type logger:           logging.Logger
    """
    pluginType = 'script'

    name = PluginAttribute(attrType=str, defaultValue='')
    description = PluginAttribute(attrType=str, defaultValue='')
    category = PluginAttribute(attrType=str, defaultValue='General')
    subcategory = PluginAttribute(attrType=str, defaultValue='')
    continueOnFail = PluginAttribute(attrType=bool, defaultValue=False)
    allowedFailures = PluginAttribute(attrType=int, defaultValue=0)
    logToFile = PluginAttribute(attrType=bool, defaultValue=True)

    def __init__(self, manager, **kwargs):
        PluginBase.__init__(self, check_dependencies=False, **kwargs)

        self._manager = manager

        if not self.continueOnFail:
            self.allowedFailures = 0

        self._scriptThread = None
        self._runLock = threading.Lock()
        self._results = []
        self._status = ''
        self._progress = 0

        self.__logger = logging.getLogger('labtronyx.%s' % self.uuid)
        self._formatter = logging.Formatter('%(asctime)s %(levelname)-8s - %(message)s')
        # Memory handler
        self._handler_mem = RotatingMemoryHandler(100)
        self._handler_mem.setFormatter(self._formatter)
        self.__logger.addHandler(self._handler_mem)
        # ZMQ Event handler
        self._handler_evt = CallbackLogHandler(
            lambda record: self.manager._publishEvent(events.EventCodes.script.log, self.uuid, record)
        )
        self._handler_evt.setFormatter(self._formatter)
        self.__logger.addHandler(self._handler_evt)
        # File handler
        self._handler_file = None

    @property
    def manager(self):
        return self._manager

    @property
    def result(self):
        return self._results

    @result.setter
    def result(self, new_result):
        if isinstance(new_result, ScriptResult):
            self._results.append(new_result)

        else:
            raise TypeError("Result must be a ScriptResult type")

    @property
    def logger(self):
        return self.__logger

    @property
    def current_test_result(self):
        return self._scriptThread.result

    def createFileLogHandler(self, filename=None):
        """
        Create a file log handler to store script logs. Called automatically by the default :func:`setUp` method if
        logToFile is True. Removes any existing file log handlers.

        :param filename: filename of new log file
        :type filename: str
        """
        if self._handler_file is not None:
            self.__logger.removeHandler(self._handler_file)

        if filename is None:
            filename = time.strftime("%Y%m%d-%H%M%S-" + self.fqn + ".log")

            try:
                import appdirs
                dirs = appdirs.AppDirs("Labtronyx", roaming=True)
                log_path = dirs.user_log_dir
                if not os.path.exists(log_path):
                    os.makedirs(log_path)
                filename = os.path.join(log_path, filename)

            except:
                pass

        self.logger.info("Logging to file: %s", filename)
        self._handler_file = logging.FileHandler(filename)
        self._handler_file.setFormatter(self._formatter)
        self.__logger.addHandler(self._handler_file)

    def getLog(self):
        """
        Get the last 100 log entries

        :return: list
        """
        return [self._handler_mem.format(record) for record in self._handler_mem.buffer]

    def _validateParameters(self):
        """
        Validate script parameters

        :return: List of failure reasons, if any
        :rtype: list[str]
        """
        params = self._getClassAttributesByBase(ScriptParameter)
        fails = []

        for attr_name, attr_cls in params.items():
            try:
                attr_cls.validate(getattr(self, attr_name))

            except Exception as e:
                fails.append("ERROR: Script parameter %s %s" % (attr_name, e.message))

        return fails

    @classmethod
    def getParameterInfo(cls):
        param_classes = cls._getClassAttributesByBase(ScriptParameter)
        return {p_name: p_cls.getDict() for p_name, p_cls in param_classes.items()}

    def getParameters(self):
        """
        Get script instance parameters

        :rtype: dict{str: object}
        """
        param_classes = self._getClassAttributesByBase(ScriptParameter)
        return {attr_name: self._getAttributeValue(attr_name) for attr_name in param_classes}

    @classmethod
    def getResourceInfo(cls):
        param_classes = cls._getClassAttributesByBase(RequiredResource)
        return {p_name: p_cls.getDict() for p_name, p_cls in param_classes.items()}

    def resolveResources(self):
        """
        Attempt to resolve all resource dependencies by iterating through all RequiredResource attributes and finding
        matching resource objects
        """
        self._resolveDependencies(check_dependencies=False)

    def _validateResources(self):
        """
        Validate resource dependencies.

        :return: List of failure reasons, if any
        :rtype: list[str]
        """
        req_res = self.getResourceResolutionInfo()
        fails = []

        for attr_name, res_list in req_res.items():
            if len(res_list) == 0:
                fails.append("ERROR: Required resource %s could not resolve to any resource" % attr_name)

            elif len(res_list) > 1:
                fails.append("ERROR: Required resource %s matches more than one resource" % attr_name)

        return fails

    def assignResource(self, res_attribute, res_uuid):
        """
        Assign a resource with a given uuid to the script attribute `res_attribute`. Used if a resource could not be
        resolved to a single resource.

        :param res_attribute: Script attribute name
        :param res_uuid: Resource UUID
        :raises: KeyError if res_attribute is not a valid RequiredResource attribute
        :raises: ResourceUnavailable if res_uuid is not a valid resource
        """
        res_info = self.getResourceResolutionInfo()
        plug = self.manager.plugin_manager.getPluginInstance(res_uuid)

        if res_attribute not in res_info:
            raise KeyError("Resource attribute is not valid")

        if plug is None:
            raise ResourceUnavailable("Resource could not be found")

        setattr(self, res_attribute, plug)
        self.manager._publishEvent(events.EventCodes.script.changed, self.uuid)

    def getResourceResolutionInfo(self):
        """
        Get RequiredResource resolution information. Returns a dict with the attribute names as the keys and a list of
        resolve Resource UUIDs as the value.

        :rtype: dict{str: list}
        """
        res_dict = {}

        for attr_name, resolution in self._getAttributesByBase(RequiredResource).items():
            if issubclass(type(resolution), ResourceBase):
                # Resolved correctly
                res_dict[attr_name] = [resolution.uuid]

            elif type(resolution) in [list, tuple]:
                res_dict[attr_name] = [res.uuid for res in resolution]

        return res_dict

    @classmethod
    def getClassAttributes(cls):
        attr = super(ScriptBase, cls).getClassAttributes()
        attr['resources'] = cls.getResourceInfo()
        attr['parameters'] = cls.getParameterInfo()
        return attr

    def getProperties(self):
        """
        Get script instance properties

        :rtype: dict{str: object}
        """
        props = super(ScriptBase, self).getProperties()
        props.update(self.getAttributes())
        props.update({
            'ready': self.isReady(),
            'running': self.isRunning(),
            'status': self._status,
            'progress': self._progress,
            'results': [result.toDict() for result in self.result],
            'resources': self.getResourceResolutionInfo()
        })
        return props

    def isReady(self):
        """
        Check if a script is ready to run. In order to run, a script must meet the following conditions:

           * All resource dependencies must be resolved.

        :return: True if ready, False if not ready
        :rtype: bool
        """
        return len(self._validateResources()) == 0

    def isRunning(self):
        """
        Check if the script is currently running.

        :rtype: bool
        """
        running = self._runLock.acquire(False)

        if running:  # lock was acquired
            self._runLock.release()

        return not running

    def start(self):
        """
        Script run routine to be called when executing the script. Returns the script result as a `ScriptResult` object.
        `run` is protected from multiple thread execution using a lock.

        :rtype:     ScriptResult
        """
        if self.isRunning():
            raise RuntimeError("Script already running")

        self._scriptThread = ScriptThread(self)
        self._scriptThread.setDaemon(True)
        self._scriptThread.start()

    def stop(self):
        """
        Stop a script that is running.

        :return: True if script was stopped
        :rtype: bool
        """
        if self.isRunning():
            return self._scriptThread.kill(ScriptStopException)

    def setUp(self):
        """
        Method called to prepare the script for execution. `setUp` is called immediately before `run`. Any exception
        raised will cause script FAILURE and the `run` method will not be called.

        Default behavior is to validate all `RequiredResource` and `ScriptParameter` objects and FAIL script if
        resources could not be resolved or required parameters were not found.

        This method can be overriden to change the behavior.
        """
        if self.logToFile:
            self.createFileLogHandler()

        self._handler_mem.flush()  # Clear log buffer
        self.logger.info("Running script: %s", self.fqn)

        spinUpFailures = []

        spinUpFailures += self._validateParameters()
        spinUpFailures += self._validateResources()

        for error_str in spinUpFailures:
            self.logger.error(error_str)

        if len(spinUpFailures) > 0:
            self.fail("Errors encountered during script setUp", True)

        # Notify that the script is running now
        self.setProgress(0)
        self.setStatus('Running')

    def tearDown(self):
        """
        Method called after `run` has been called and after `onPass`, `onSkip` or `onFail` have been called, depending
        on the result of the script.

        Default behavior is to log script completion information like script result, failure reason, execution time,
        etc.

        This method can be overriden to change the behavior.
        """
        self.setProgress(100)
        self.setStatus('Finished')

        self.manager._publishEvent(events.EventCodes.script.finished, self.uuid)

        if self.current_test_result.executionTime > 0:
            self.logger.info("Script Execution Time: %f", self.current_test_result.executionTime)

        self.logger.info("Script Result: %s", self.current_test_result.result)
        if self.current_test_result.result == ScriptResult.FAIL:
            self.logger.info("Failure Reason: %s", self.current_test_result.reason)
            self.logger.info("Failure Count: %d", self.current_test_result.failCount)

    def run(self):
        """
        Main script body, override this method in script subclasses to put all code. Any exceptions raised will be
        handled and may cause script FAILURE (depending on behavior of `onException`).
        """
        pass

    def onException(self, e):
        """
        Method called when an unhandled exception is caught. Default behavior is to log the exception and FAIL the
        script. When called, script execution has already halted, there is no way to continue execution.

        This method can be overriden to change the behavior.

        :param e:   Exception caught
        :type e:    Exception
        """
        self.current_test_result.result = ScriptResult.FAIL
        self.current_test_result.addFailure("Unhandled Exception: %s" % type(e))

        self.logger.exception(self.current_test_result.reason)

    def onPass(self):
        """
        Method called when a script execution has finished with a PASS status. Default behavior is to do nothing.

        This method can be overriden to change the behavior.
        """
        pass

    def onSkip(self):
        """
        Method called when a script is halted due to a SKIP condition. Default behavior is to do nothing.

        This method can be overriden to change the behavior.
        """
        pass

    def onFail(self):
        """
        Method called when a script is halted due to a FAIL condition. Called after `onException` (if applicable) but
        before `tearDown`. Default behavior is to do nothing.

        This method can be overriden to change the behavior.
        """
        pass

    def setProgress(self, new_progress):
        """
        Optional method to set the progress of a script. Useful for external tools or GUIs to report script progress.

        :param new_progress:    Progress (out of 100)
        :type new_progress:     int
        """
        self._progress = max(0, min(int(new_progress), 100))
        self.manager._publishEvent(events.EventCodes.script.changed, self.uuid)

    def setStatus(self, new_status):
        """
        Optional method to set the text status of the script. Useful for external tools or GUIs to report script status.
        Use in conjunction with `setProgress`

        :param new_status:      Status
        :type new_status:       str
        """
        self._status = str(new_status)
        self.manager._publishEvent(events.EventCodes.script.changed, self.uuid)

    def fail(self, reason, stop=False):
        """
        Set the script result to FAIL. Execution will halt on the following conditions:

           * `continueOnFail` attribute is False
           * `allowedFailures` attribute has been exceeded
           * `stop` parameter is True

        :param reason:          Reason for script failure
        :type reason:           str
        :param stop:            Flag to stop script execution
        :type stop:             bool
        """
        self.current_test_result.result = ScriptResult.FAIL
        self.current_test_result.addFailure(reason)

        self.logger.info("FAILURE: %s", reason)

        if stop:
            raise ScriptStopException("Script failure, see failure reason")
        elif self.current_test_result.failCount > self.allowedFailures:
            raise ScriptStopException("Failure count exceeded allowed failures")

    def skip(self, reason):
        """
        Set the script result to SKIP and halt execution.

        :param reason:          Reason for script failure
        :type reason:           str
        """
        self.current_test_result.result = ScriptResult.SKIP
        self.current_test_result.addFailure(reason)

        raise ScriptStopException("Skipped")

    def assertEqual(self, a, b, msg=None):
        self.expectEqual(a, b, msg, True)

    def assertNotEqual(self, a, b, msg=None):
        self.expectNotEqual(a, b, msg, True)

    def assertTrue(self, a, msg=None):
        self.expectTrue(a, msg, True)

    def assertFalse(self, a, msg=None):
        self.expectFalse(a, msg, True)

    def assertIn(self, object, container, msg=None):
        self.expectIn(object, container, msg, True)

    def assertNotIn(self, object, container, msg):
        self.expectNotIn(object, container, msg, True)

    def expectEqual(self, a, b, msg=None, stop=False):
        if msg is None:
            msg = "%s != %s" % (a, b)

        if a != b:
            self.fail(msg, stop)

    def expectNotEqual(self, a, b, msg=None, stop=False):
        if msg is None:
            msg = "%s == %s" % (a, b)

        if a == b:
            self.fail(msg, stop)

    def expectTrue(self, a, msg=None, stop=False):
        if msg is None:
            msg = "%s is not True" % a

        if not a:
            self.fail(msg, stop)

    def expectFalse(self, a, msg=None, stop=False):
        if msg is None:
            msg = "%s is not False" % a

        if a:
            self.fail(msg, stop)

    def expectIn(self, object, container, msg=None, stop=False):
        if msg is None:
            msg = "%s not in %s" % (object, container)

        if object not in container:
            self.fail(msg, stop)

    def expectNotIn(self, object, container, msg=None, stop=False):
        if msg is None:
            msg = "%s in %s" % (object, container)

        if object in container:
            self.fail(msg, stop)


class ScriptThread(threading.Thread):
    def __init__(self, scriptObj):
        assert (isinstance(scriptObj, ScriptBase))
        super(ScriptThread, self).__init__()

        self.__scriptObj = scriptObj
        self.__scriptResult = ScriptResult()

        self.setName('ScriptThread-%s' % self.script.uuid)

    @property
    def script(self):
        return self.__scriptObj

    @property
    def result(self):
        return self.__scriptResult

    def kill(self, exc_type):
        """
        Called asyncronously to kill a thread by raising an exception using the Python API and ctypes.

        .. note::

           If there is a profiler or debugger attached to the Python interpreter, there is a high chance this will
           not work.

        :param exc_type: Exception to throw
        :type exc_type: type(Exception)
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(exc_type))

            if res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
                return False

            else:
                return True

    def run(self):
        self.result.startTimer()

        lockAcq = self.script._runLock.acquire(False)
        if not lockAcq:
            raise threading.ThreadError

        try:
            self.script.setUp()

            self.script.run()

        except ScriptStopException as e:
            self.script.logger.info("Script Stopped: %s", e.message)
            self.result.result = ScriptResult.STOPPED
            self.result.reason = "Script stopped"

        except Exception as e:
            # Handle all uncaught exceptions
            self.script.onException(e)

        finally:
            if self.result.result == ScriptResult.PASS:
                self.script.onPass()
            elif self.result.result == ScriptResult.FAIL:
                self.script.onFail()
            elif self.result.result == ScriptResult.SKIP:
                self.script.onSkip()

            self.script.tearDown()

            self.script._runLock.release()

            self.result.stopTimer()
            self.script.result = self.result


class RequiredResource(PluginDependency):
    def __init__(self, **kwargs):
        kwargs['pluginType'] = 'resource'
        super(RequiredResource, self).__init__(**kwargs)

    def getDict(self):
        return self.attrs


class ScriptParameter(PluginParameter):
    pass


class ScriptResult(object):
    PASS = 'PASS'
    FAIL = 'FAIL'
    SKIP = 'SKIP'
    STOPPED = 'STOPPED'

    def __init__(self):
        self._result = self.PASS
        self._reason = ''
        self._startTime = 0
        self._stopTime = 0

        self._failures = []

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        if value in [self.PASS, self.FAIL, self.SKIP, self.STOPPED]:
            self._result = value
        else:
            raise ValueError("Invalid result type")

    @property
    def reason(self):
        if self._reason != '':
            return self._reason
        else:
            # Latest failure
            if len(self._failures) > 0:
                return self._failures[-1]

            else:
                return ''

    @reason.setter
    def reason(self, value):
        self._reason = value

    @property
    def failCount(self):
        return len(self._failures)

    def addFailure(self, msg):
        self._failures.append(msg)

    def startTimer(self):
        self._startTime = time.time()

    def stopTimer(self):
        self._stopTime = time.time()

    @property
    def startTime(self):
        return self._startTime

    @property
    def executionTime(self):
        return self._stopTime - self._startTime

    def toDict(self):
        return {
            'time': self.startTime,
            'result': self.result,
            'reason': self.reason,
            'failCount': self.failCount,
            'executionTime': self.executionTime
        }


class ScriptStopException(RuntimeError):
    pass


class RotatingMemoryHandler(BufferingHandler):
    def emit(self, record):
        self.buffer.append(record)
        if len(self.buffer) > self.capacity:
            del self.buffer[0]


class CallbackLogHandler(logging.Handler):
    def __init__(self, callback):
        logging.Handler.__init__(self)
        self._callback = callback

    def emit(self, record):
        self._callback(self.format(record))
