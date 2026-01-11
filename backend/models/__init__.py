from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .document import Document
from .template import Template
from .application import Application
from .api_key import APIKey
from .purchase import Purchase

__all__ = ['db', 'User', 'Document', 'Template', 'Application', 'APIKey', 'Purchase']
