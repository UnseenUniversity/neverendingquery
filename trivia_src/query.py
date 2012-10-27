
from google.appengine.ext import db

class Query( db.Expando ):

    id = db.StringProperty()