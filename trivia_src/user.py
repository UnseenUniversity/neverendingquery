

from google.appengine.ext import db


class User(db.Expando):

    ''' Keeps user related information '''
    author = db.StringProperty()
    email  = db.StringProperty()

    