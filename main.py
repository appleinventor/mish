#!/usr/bin/env python
'''
    Minecraft Interactive Server Helper (mish) - By Andy Merrill

    mish is a simple yet powerful Minecraft server manager written is Python.
'''

# TODO: Create datebase setup script as end-users will have to install MySQL on their own
### sdl imports ###
import os
import sys
import time

### Flask imports ###
from flask import Flask, render_template, request, url_for, redirect, render_template_string, abort, g, make_response, request
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter, roles_required
from werkzeug import secure_filename

### Other imports ###
import psutil
import bitmath
import wget
import libtmux

# Use a Class-based config to avoid needing a 2nd file
# os.getenv() enables configuration through OS environment variables
class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///mish.sqlite')
    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'mtklabs@gmail.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        'pioneers69276&unaccountableness')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"mish" <noreply@localhost>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'smtp.gmail.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '465'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         True))

    # Flask-User settings
    USER_APP_NAME        = "mish"                # Used by email templates
    USER_ENABLE_LOGIN_WITHOUT_CONFIRM_EMAIL = True
    USER_ENABLE_CONFIRM_EMAIL      = True
    USER_AFTER_LOGIN_ENDPOINT = 'dashboard'


def create_app(test_config=None):                   # For automated tests
    # Setup Flask and read config from ConfigClass defined above
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')
    print(app.config)

    # Load local_settings.py if file exists         # For automated tests
    try:
        app.config.from_object('local_settings')
    except:
        pass

    # Load optional test_config                     # For automated tests
    if test_config:
        app.config.update(test_config)

    # Initialize Flask extensions
    mail = Mail(app)                                # Initialize Flask-Mail
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy

    # Define the User data model. Make sure to add flask_user UserMixin!!
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)

        # User authentication information
        username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User email information
        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())

        # User information
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        first_name = db.Column(db.String(100), nullable=False, server_default='')
        last_name = db.Column(db.String(100), nullable=False, server_default='')

        # Relationships
        roles = db.relationship('Role', secondary='user_roles',
                backref=db.backref('users', lazy='dynamic'))

    # Define the Role data model
    class Role(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles data model
    class UserRoles(db.Model):
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

    # Reset all the database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db,  User)
    user_manager = UserManager(db_adapter, app)

    # Create 'user007' user with 'secret' and 'agent' roles
    if not User.query.filter(User.username=='admin').first():
        owner = User(username='admin', email='andy@the15thshell.com', active=True,
                password=user_manager.hash_password('adminPassword1'))
        owner.roles.append(Role(name='owner'))
        db.session.add(owner)
        db.session.commit()


    ### Data functions ###
    def disk_usage(poll):
        du = psutil.disk_usage('/')
        if poll == 'pct':
            return du[3]
        elif poll == 'use':
            return str(int(bitmath.Byte(du[1]).to_GB())) + ' / ' + str(int(bitmath.Byte(du[0]).to_GB())) + ' GB'

    ### Flask routes ###
    @app.route('/')
    def index():
        return redirect(url_for('user.login'))
        # abort(418)

    @app.route('/dashboard', methods=['GET', 'POST'])
    @login_required
    def dashboard():
        return render_template('index.html', disk_pct=disk_usage('pct'), disk_use=disk_usage('use'))

    @app.route('/brew', methods=['GET', 'POST'])
    def brew():
        if request.method == 'POST':
            return 'Put brew egg here'
        else:
            abort(418)

    ## Server specific routes ##
    # TODO: Build templates for all server routes
    @app.route('/server/<server_name>/', methods=['GET', 'POST'])
    @login_required
    def server(server_name):
        return server_name

    @app.route('/server/<server_name>/stop', methods=['GET', 'POST'])
    def server_stop(server_name):
        # TODO: Replace with redirect back to server page
        # TODO: Actually stop specified server
        return 'Stopping server \'{}\''.format(server_name)

    @app.route('/server/<server_name>/start', methods=['GET', 'POST'])
    def server_start(server_name):
        # TODO: Replace with redirect back to server page
        # TODO: Actually start specified server
        return 'Starting server \'{}\''.format(server_name)

    @app.route('/server/<server_name>/console', methods=['GET', 'POST'])
    def server_rcon(server_name):
        # TODO: Actually RCON to server. Might be difficult with BungeeCord
        return 'Console'

    @app.route('/server/<server_name>/plugins', methods=['GET', 'POST'])
    def server_plugins(server_name):
        # TODO: Create plugin list
        # TODO: Add/remove Plugins
        return 'Plugins'

    @app.route('/server/<server_name>/files', methods=['GET', 'POST'])
    def server_files(server_name):
        # TODO: Show list of files in server directory
        return 'Files'

    @app.route('/server/<server_name>/plugins/<plugin>', methods=['GET', 'POST'])
    def server_plugin(server_name, plugin):
        # TODO: Plugin config
        return '{}: {}'.format(server_name, plugin)

    return app

### Main loop ###
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True, port=5000)
