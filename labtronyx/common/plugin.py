from yapsy.PluginFileLocator import IPluginFileAnalyzer

class LabtronyxPluginAnalyzer(IPluginFileAnalyzer):

    def isValidPlugin(self, filename):
        """
        Valid plugins:

           - Have a module-level `info` dictionary
           - Have a class that extends BasePlugin

        :param filename:
        :return:
        """
        pass

    def getInfosDictFromPlugin(self, dirpath, filename):
        pass

