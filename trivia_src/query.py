
from google.appengine.ext import db

class Query( db.Model ):

    text   = db.StringProperty( multiline = True)
    answer = db.StringProperty()
    
    date   = db.DateProperty( auto_now_add = True )
    
    category = db.CategoryProperty() 
    tags     = db.StringListProperty()
    
    fake_answers = db.StringListProperty()
    
class EntityCounter( db.Model ):
    
    counter = db.IntegerProperty()