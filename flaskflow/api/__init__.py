# This file is part of the Reproducible and Reusable Data Analysis Workflow
# Server (flowServ).
#
# Copyright (C) 2019-2020 NYU.
#
# flowServ is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Flask Application Factory. Initalize the Flask application that serves the
ROB web API.
"""

import logging
import os
import sys

from flask import Flask, jsonify, make_response
from flask_cors import CORS
from logging.handlers import RotatingFileHandler

import flowserv.error as err
import flaskflow.error as rob
import flaskflow.config as config


root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


def create_app(test_config=None):
    """Initialize the Flask application."""
    # Create tha app. Follwoing the Twelve-Factor App methodology we configure
    # the Flask application from environment variables.
    app = Flask(__name__, instance_relative_config=True)
    if test_config is not None:
        app.config.update(test_config)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH()
    # Enable CORS
    CORS(app)
    # --------------------------------------------------------------------------
    # Initialize error logging
    # --------------------------------------------------------------------------
    # Use rotating file handler for server logs
    logdir = config.LOG_DIR()
    os.makedirs(config.LOG_DIR(), exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(logdir, 'flaskflow.log'),
        maxBytes=1024 * 1024 * 100,
        backupCount=20
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    app.logger.addHandler(file_handler)

    # --------------------------------------------------------------------------
    # Define error handlers
    # --------------------------------------------------------------------------
    @app.errorhandler(err.ConstraintViolationError)
    def invalid_request_action(error):
        """JSON response handler for requests that violate an application
        constraint.

        Parameters
        ----------
        error : Exception
            Exception thrown by request Handler

        Returns
        -------
        Http response
        """
        return make_response(jsonify({'message': str(error)}), 400)

    @app.errorhandler(rob.InvalidRequestError)
    def invalid_request_body(error):
        """JSON response handler for requests that do not contain a valid
        request body.

        Parameters
        ----------
        error : Exception
            Exception thrown by request Handler

        Returns
        -------
        Http response
        """
        return make_response(jsonify({'message': str(error)}), 400)

    @app.errorhandler(err.UnauthenticatedAccessError)
    def unauthenticated_access(error):
        """JSON response handler for unauthenticated requests.

        Parameters
        ----------
        error : Exception
            Exception thrown by request Handler

        Returns
        -------
        Http response
        """
        return make_response(jsonify({'message': str(error)}), 403)

    @app.errorhandler(err.UnauthorizedAccessError)
    def unauthorized_access(error):
        """JSON response handler for unauthorized requests.

        Parameters
        ----------
        error : Exception
            Exception thrown by request Handler

        Returns
        -------
        Http response
        """
        return make_response(jsonify({'message': str(error)}), 403)

    @app.errorhandler(err.UnknownObjectError)
    def resource_not_found(error):
        """JSON response handler for requests that access unknown resources.

        Parameters
        ----------
        error : Exception
            Exception thrown by request Handler

        Returns
        -------
        Http response
        """
        return make_response(jsonify({'message': str(error)}), 404)

    @app.errorhandler(413)
    def upload_error(error):
        """Exception handler for file uploads that exceed the file size
        limit.
        """
        app.logger.error(error)
        return make_response(jsonify({'error': str(error)}), 413)

    @app.errorhandler(500)
    def internal_error(error):
        """Exception handler that logs internal server errors."""
        app.logger.error(error)
        return make_response(jsonify({'error': str(error)}), 500)

    # --------------------------------------------------------------------------
    # Import blueprints for App components
    # --------------------------------------------------------------------------
    # Workflow Service
    import flaskflow.api.workflow as workflow
    app.register_blueprint(workflow.bp)
    # File Upload Service
    # import flaskflow.api.user as users
    # app.register_blueprint(users.bp)
    # Run Service
    # import flaskflow.api.run as runs
    # app.register_blueprint(runs.bp)
    # Return the app
    return app
