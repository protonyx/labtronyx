__author__ = 'kkennedy'

from flask import Flask, Blueprint, request, current_app

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
    pass

@api_blueprint.route('/api/resources/<uuid>')
def resource_properties(uuid):
    pass

@api_blueprint.route('/api/version')
def version():
    man = current_app.config.get('MANAGER_INSTANCE')

    return man.getVersion()

@api_blueprint.route('/api/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        func()
    return ''

@rpc_blueprint.route('/rpc/<uuid>')
def rpc_process(uuid):
    pass

