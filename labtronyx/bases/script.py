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
import time
import threading, ctypes

# Package relative imports
from ..common import events
from ..common.errors import *
from ..common.plugin import PluginBase, PluginAttribute

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

    def __init__(self, manager, **kwargs):
        PluginBase.__init__(self, **kwargs)

        self._manager = manager

        if not self.continueOnFail:
            self.allowedFailures = 0

        # Resolve all ScriptParameters using keyword arguments
        # script runner is responsible for passing CLI args as a dict
        self._resolveParameters(**kwargs)

        self._scriptThread = None
        self._runLock = threading.Lock()
        self._results = []
        self._status = ''
        self._progress = 0

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
    def current_test_result(self):
        return self._scriptThread.result

    def _collectRequiredResources(self):
        req_res = self._getClassAttributesByBase(RequiredResource)
        res = {}

        for attr_name, attr_cls in req_res.items():
            matching_res = self._manager.findResources(**attr_cls.search_params)
            res[attr_name] = matching_res

        return res

    def _resolveResources(self):
        """
        Iterate through all RequiredResource attributes and replace instance attributes with resource objects.
        """
        req_res = self._collectRequiredResources()

        for attr_name, res_list in req_res.items():
            if len(res_list) == 0 or len(res_list) > 1:
                setattr(self, attr_name, None)
            else:
                setattr(self, attr_name, res_list[0])

    def _validateResources(self):
        req_res = self._collectRequiredResources()
        failCount = 0

        for attr_name, res_list in req_res.items():
            if len(res_list) == 0:
                self.logger.info("ERROR: Required resource %s could not be found", attr_name)
                failCount += 1

            elif len(res_list) > 1:
                self.logger.info("ERROR: Required resource %s ")
                failCount += 1

        return failCount

    def _resolveParameters(self, **kwargs):
        params = self._getClassAttributesByBase(ScriptParameter)

        # TODO: Resolve command line parameters as well

        for attr_name, attr_cls in params.items():
            attr_val = kwargs.get(attr_name)

            if attr_val is None:
                setattr(self, attr_name, attr_cls.defaultValue)
            else:
                setattr(self, attr_name, attr_val)

    def _validateParameters(self):
        params = self._getClassAttributesByBase(ScriptParameter)
        failCount = 0

        for attr_name, attr_cls in params.items():
            try:
                attr_cls.validate(getattr(self, attr_name))

            except Exception as e:
                self.logger.info("ERROR: Script parameter %s %s", attr_name, e.message)
                failCount += 1

        return failCount

    def assignResource(self, res_attribute, res_uuid):
        # TODO: Implement this feature
        raise NotImplementedError

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

        param_vals = {}

        for attr_name, attr_obj in param_classes.items():
            param_vals[attr_name] = getattr(self, attr_name, None)

        return param_vals

    def getProperties(self):
        """
        Get script instance properties

        :rtype: dict{str: object}
        """
        props = super(ScriptBase, self).getProperties()
        props.update(self.getAttributes())
        props.update(self.getParameters())
        props.update({
            'running': self.isRunning(),
            'status': self._status,
            'progress': self._progress,
            'results': [result.toDict() for result in self.result]
        })
        return props

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

        # Wait for the script to finish
        # self._scriptThread.join()

        # self._scriptThread = None

    def stop(self):
        if self.isRunning():
            self._scriptThread.kill(ScriptStopException)

    def setUp(self):
        """
        Method called to prepare the script for execution. `setUp` is called immediately before `run`. Any exception
        raised will cause script FAILURE and the `run` method will not be called.

        Default behavior is to validate all `RequiredResource` and `ScriptParameter` objects and FAIL script if
        resources could not be resolved or required parameters were not found.

        This method can be overriden to change the behavior.
        """
        self.logger.info("Running script: %s", self.__class__.__name__)

        for res_uuid, res_dict in self._manager.getProperties().items():
            self.logger.info("Found resource: %s", res_dict.get('resourceID'))

        spinUpFailures = 0

        spinUpFailures += self._validateParameters()
        spinUpFailures += self._validateResources()

        if spinUpFailures > 0:
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
        assert(isinstance(scriptObj, ScriptBase))
        super(ScriptThread, self).__init__()

        self.__scriptObj = scriptObj
        self.__scriptResult = ScriptResult()

    @property
    def script(self):
        return self.__scriptObj

    @property
    def result(self):
        return self.__scriptResult

    def kill(self, exc_type):
        """
        Called asyncronously to kill a thread by raising an exception

        :param exc_type:
        :type exc_type:
        :return:
        :rtype:
        """
        if self.isAlive():
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(exc_type))

            if res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
                raise RuntimeError("Unable to kill thread")

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


class RequiredResource(object):
    def __init__(self, **kwargs):
        self.search_params = kwargs


class ScriptParameter(object):
    def __init__(self, attrType=str, required=False, defaultValue=None, description=''):
        self.attrType = attrType
        self.required = required
        self.defaultValue = defaultValue
        self.description = description

    def validate(self, value):
        if self.required and value is None:
            raise ValueError("is required")

        if type(value) != self.attrType:
            # Can we cast?
            try:
                self.attrType(value)

            except:
                raise TypeError("must be of type %s" % self.attrType)

    def getDict(self):
        return {
            'description': self.description,
            'required': self.required
        }


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
        if value in [self.PASS, self.FAIL, self.SKIP]:
            self._result = value
        else:
            raise ValueError("Invalid result type")

    @property
    def reason(self):
        if self._reason != '':
            return self._reason
        else:
            # Latest failure
            return self._failures[-1]

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
    def executionTime(self):
        return self._stopTime - self._startTime

    def toDict(self):
        return {
            'result': self.result,
            'reason': self.reason,
            'failCount': self.failCount,
            'executionTime': self.executionTime
        }


class ScriptStopException(RuntimeError):
    pass