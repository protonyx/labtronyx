"""
Labtronyx Flask app factory

Call `create_server` to get a flask app
"""

__author__ = 'kkennedy'

import logging

from flask import Flask, Blueprint, request, current_app, abort, Response
import json

from .rpc import *

api_blueprint = Blueprint('api', __name__)
rpc_blueprint = Blueprint('rpc', __name__)

def create_server(manager_instance, port, logger=logging):
    """
    Labtronyx Server Factory

    :param manager_instance:
    :param port:
    :return:
    """
    app = Flask(__name__)

    app.config['LABTRONYX_MANAGER'] = manager_instance
    app.config['LABTRONYX_LOGGER'] = logger

    app.register_blueprint(api_blueprint)
    app.register_blueprint(rpc_blueprint)

    return app

@api_blueprint.route('/api/resources')
def list_resources():
    man = current_app.config.get('LABTRONYX_MANAGER')

    data = json.dumps(man.getProperties())

    resp = Response(data, status=200, mimetype='application/json')

    return resp

@api_blueprint.route('/api/resources/<uuid>')
def resource_properties(uuid):
    man = current_app.config.get('LABTRONYX_MANAGER')

    props = man.getProperties()

    if uuid in props:
        return json.dumps(props.get(uuid))

    else:
        abort(404)

@api_blueprint.route('/api/version')
def version():
    man = current_app.config.get('LABTRONYX_MANAGER')

    try:
        return json.dumps({
            'version': man.version.ver_sem,
            'version_full': man.version.ver_full,
            'build_date': man.version.build_date,
            'git_revision': man.version.git_revision
        })

    except:
        return json.dumps({
            'version': man.getVersion()
        })

@api_blueprint.route('/api/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        func()
    return ''

@rpc_blueprint.route('/rpc', methods=['GET', 'POST'])
@rpc_blueprint.route('/rpc/<uuid>', methods=['GET', 'POST'])
def rpc_process(uuid=None):
    if request.method == 'GET':
        def rpc_getMethods(target):
            import inspect
            # Check for bound and unbound methods
            validMethod = lambda mem: inspect.ismethod(mem) or inspect.isfunction(mem)
            return [attr for attr, val in inspect.getmembers(target) if validMethod(val) and not attr.startswith('_')]

        man = current_app.config.get('LABTRONYX_MANAGER')

        if uuid is None:
            return json.dumps({
                'methods': rpc_getMethods(man)
            })

        else:
            try:
                res = man._getResource(uuid)
                return json.dumps({
                    'methods': rpc_getMethods(res)
                })

            except KeyError:
                abort(404)

    elif request.method == 'POST':
        # Set decode engine based on content type
        contentType = request.headers['Content-Type']

        if contentType == 'application/json':
            engine = jsonrpc
        else:
            engine = jsonrpc

        # Determine a target object
        man = current_app.config.get('LABTRONYX_MANAGER')
        if uuid is None:
            target = man
        else:
            try:
                target = man._getResource(uuid)
            except KeyError:
                abort(404)

        # Get lock
        import threading
        locks = current_app.config.get('RPC_LOCKS', {})
        if uuid not in locks:
            locks[uuid] = threading.Lock()
        lock = locks.get(uuid)

        # Decode the incoming data
        rpc_requests, _, rpc_errors = engine.decode(request.data)

        # Process responses
        # For now, ignore all responses
        rpc_responses = []

        # Process requests
        if len(rpc_errors) != 0:
            # Process errors
            for err in rpc_errors:
                # Move errors into the responses list
                rpc_responses.append(err)

        else:
            # Only process requests if no errors were encountered
            if len(rpc_requests) > 0:
                pass

            for req in rpc_requests:
                method_name = req.method
                req_id = req.id

                try:
                    with lock:
                        # RPC hook for target objects, allows the object to dispatch the request
                        if hasattr(target, '_rpc'):
                            result = target._rpc(method_name)

                        elif not method_name.startswith('_') and hasattr(target, method_name):
                            method = getattr(target, method_name)
                            result = req.call(method)

                        else:
                            rpc_responses.append(RpcMethodNotFound(id=req_id))
                            break

                    # Check if the request was a notification
                    if req_id is not None:
                        rpc_responses.append(RpcResponse(id=req_id, result=result))

                # Catch exceptions during method execution
                except Exception as e:
                    excp = RpcServerException(id=req_id)
                    # Pass the type as the message so the client can attempt to match with a client-side exception
                    excp.message = '{}|{}'.format(e.__class__.__name__, e.message)
                    rpc_responses.append(excp)

                    # Log the exception on the server
                    logger = current_app.config.get('LABTRONYX_LOGGER')
                    logger.exception('RPC Server-side Exception')

        # Encode the outgoing data
        try:
            out_data = engine.encode([], rpc_responses)

        except Exception as e:
            # Encoder errors are RPC Errors
            out_data = engine.encode([], [RpcError()])

        return out_data

