__author__ = 'kkennedy'

__all__ = ['jsonrpc']

class RpcRequest(object):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.method = kwargs.get('method', '')
        self.args = kwargs.get('args', [])
        self.kwargs = kwargs.get('kwargs', {})

    def call(self, target):
        # Invoke target method with stored arguments
        # Don't attempt to catch exceptions here, let them bubble up
        return target(*self.args, **self.kwargs)

class RpcResponse(object):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.result = kwargs.get('result', None)