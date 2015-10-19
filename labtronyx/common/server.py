__author__ = 'kkennedy'

from flask import Flask, Blueprint, request, current_app, abort
import json

api_blueprint = Blueprint('api', __name__)
rpc_blueprint = Blueprint('rpc', __name__)

def create_server(manager_instance, port):
    """
    Labtronyx Server Factory

    :param manager_instance:
    :param port:
    :return:
    """
    app = Flask(__name__)

    app.config['MANAGER_INSTANCE'] = manager_instance

    app.register_blueprint(api_blueprint)
    app.register_blueprint(rpc_blueprint)

    return app

@api_blueprint.route('/api/resources')
def list_resources():
    man = current_app.config.get('MANAGER_INSTANCE')

    return str(man.getProperties().keys())

@api_blueprint.route('/api/resources/<uuid>')
def resource_properties(uuid):
    man = current_app.config.get('MANAGER_INSTANCE')

    props = man.getProperties()

    if uuid in props:
        return str(props.get(uuid))

    else:
        abort(404)

@api_blueprint.route('/api/version')
def version():
    man = current_app.config.get('MANAGER_INSTANCE')

    try:
        return json.dump({
            'version': man.version.ver_sem,
            'version_full': man.version.ver_full,
            'build_date': man.version.build_date,
            'git_revision': man.version.git_revision
        })

    except:
        return json.dump({
            'version': man.getVersion()
        })

@api_blueprint.route('/api/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        func()
    return ''

@rpc_blueprint.route('/rpc')
@rpc_blueprint.route('/rpc/<uuid>')
def rpc_process(uuid):
    engine = self.server.engine
    target = self.server.rpc_paths.get(self.path)
    lock   = self.server.rpc_locks.get(self.path)

    # Decode the incoming data
    requests, _, rpc_errors = engine.decode(data)

    # Process responses
    # For now, ignore all responses
    responses = []

    # Process requests
    if len(rpc_errors) != 0:
        # Process errors
        for err in rpc_errors:
            # Move errors into the responses list
            responses.append(err)

    else:
        # Only process requests if no errors were encountered
        if len(requests) > 0:
            pass

        for req in requests:
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
                        responses.append(RpcMethodNotFound(id=req_id))
                        break

                # Check if the request was a notification
                if req_id is not None:
                    responses.append(RpcResponse(id=req_id, result=result))

            # Catch exceptions during method execution
            # DO NOT ALLOW ANY EXCEPTIONS TO PASS THIS LEVEL
            except Exception as e:
                # Catch-all for everything else
                excp = RpcServerException(id=req_id)
                excp.message = e.__class__.__name__
                responses.append(excp)

    # Encode the outgoing data
    try:
        out_data = engine.encode([], responses)

    except Exception as e:
        # Encoder errors are RPC Errors
        out_data = engine.encode([], [RpcError()])

    return out_data

