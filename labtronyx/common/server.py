__author__ = 'kkennedy'

from flask import Flask

def create_server(manager_instance, port):
    """
    Labtronyx Server Factory

    :param manager_instance:
    :param port:
    :return:
    """
    app = Flask(__name__)



    return app