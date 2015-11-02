import labtronyx
from labtronyx.common.plugin import PluginBase, PluginAttribute

class ScriptBase(PluginBase):
    """
    Script base class, modeled after the Python unittest framework.

    Scripts are code modules that run commands sequentially from start to completion with an expected outcome. At the
    end of a script, a PASS or FAIL designation is returned depending on pre-programmed conditions within the script.
    The ScriptBase class provides a number of convenience functions to ease interaction with external instruments or
    devices through the Labtronyx framework.

    The default outcome of a script is a PASS designation. The developer is responsible for deciding when to return a
    FAILURE. FAILURES can be set explicitly by calling the `fail` method, or by using on of the convenience functions
    to FAIL on a certain condition. If the `continueOnFail` attribute is set, a FAILURE will not stop script execution,
    but the outcome of the script will be reported as FAIL. If script execution needs to be stopped on a FAILURE
    condition, the `stop` parameter of the `fail` method can be set, or any of the convenience functions beginning with
    `assert` will cause execution to halt when the condition is met.
    """
    name = PluginAttribute(attrType=str, defaultValue='')
    description = PluginAttribute(attrType=str, defaultValue='')
    continueOnFail = PluginAttribute(attrType=bool, defaultValue=False)

    def __init__(self, manager, **kwargs):
        """
        :param manager:         Reference to the InstrumentManager instance
        :type manager:          InstrumentManager object
        :param logger:          Logger
        :type logger:           Logging.logger object
        """
        PluginBase.__init__(self, **kwargs)

        if not isinstance(manager, labtronyx.InstrumentManager):
            raise EnvironmentError("manager parameter must be an instance of InstrumentManager")

    def _start(self):
        """
        Script run routine to be called when executing the script
        """
        self._scriptResult = None

        try:
            self.setUp()

            self.run()

        except Exception as e:
            self.onException()

        finally:
            # TODO: call only if failed
            self.onFail()

            self.tearDown()

    def _stop(self):
        pass

    # Script hooks
    def setUp(self):
        raise NotImplementedError()

    def tearDown(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    def onException(self):
        raise NotImplementedError()

    def onPass(self):
        raise NotImplementedError()

    def onFail(self):
        raise NotImplementedError()

    # Script functions

    def requireResource(self, name, attr_name, **kwargs):
        pass

    def setProgress(self, new_progress):
        pass

    def setStatus(self, new_status):
        pass

    # Convenience functions

    def fail(self, reason, stop=False):
        pass

    def skip(self, reason):
        pass

    def assertEqual(self, a, b, msg):
        pass

    def assertNotEqual(self, a, b, msg):
        pass

    def assertTrue(self, a, msg):
        pass

    def assertFalse(self, a, msg):
        pass

    def assertIn(self, object, container, msg):
        pass

    def assertNotIn(self, object, container, msg):
        pass

    def expectEqual(self, a, b, msg):
        pass

    def expectNotEqual(self, a, b, msg):
        pass

    def expectTrue(self, a, msg):
        pass

    def expectFalse(self, a, msg):
        pass

    def expectIn(self, object, container, msg):
        pass

    def expectNotIn(self, object, container, msg):
        pass