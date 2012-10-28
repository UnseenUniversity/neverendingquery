#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import cgi

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from sets import Set

from google.appengine.api import users
from google.appengine.ext import db

#from appengine_utilities import *

from user import *
from query import *



def get_user_entry():
    user=users.get_current_user()
    c_user=User.get(db.Key.from_path('User_data' ,user.nickname() ))
    return (user,c_data)

def get_value( object_type, key ):
    return db.Key.from_path(object_type,key);

def increase_entity_counter( entity_name ):

    Counter = EntityCounter.get( db.Key.from_path('EntityCounter',entity_name) )
    
    if Counter is None:
        Counter = EntityCounter( key_name = entity_name )
        Counter.counter = 1
    else: 
        Counter.counter += 1

    Counter.put()

def get_user_entity():
    c_user = User.get( db.Key.from_path('User', users.get_current_user().nickname() ) )
    return c_user
        

def user_init( user ):
    
    user = User( key_name = user.nickname() )
    user.put()
            
    return user


class QueryTrainer(webapp2.RequestHandler):

    def check_user(self):
        user = users.get_current_user()
        if user is None:
            self.redirect( user.create_login_url(self.request.uri) )

    def escape( self, field ):
        return cgi.escape( self.request.get(field) )

    
    def get(self):
        
        self.check_user()

        #template_values = {
        #                   'user_id': user_id,
        #                   
        #                   }
        template_values = {}

            
        template = jinja_environment.get_template('add.html')
        self.response.out.write(template.render(template_values))    
        
    def post(self):
        
        question = self.escape("question")
        if question is None:
            return
        
        db.run_in_transaction( increase_entity_counter, 'Query' )
        q_no = EntityCounter.get( db.Key.from_path('EntityCounter','Query') ).counter
 
        ans = self.escape("answer1")    
        new_query = Query( key_name = str(q_no), text = question, answer = ans )
        
        category = self.escape("category")
        if category is not None:
            new_query.category = category
        
        tags = self.escape("tags")
        if tags is not None:    
            words = tags.split(';')
            new_query.tags = words
    
        i = 2
        fake_ans = []
        while i < 4:
            ans = self.escape("answer"+str(i))
            new_query.fake_answers.append(ans)
            i +=1
            
        new_query.put()
        
        c_user = get_user_entity()
        c_user.questions.append(str(q_no))
        c_user.put()
    
        self.redirect('/train')
   
    
class MainPage(webapp2.RequestHandler):
    
    def get(self):
        
        user = users.get_current_user()
        
        if user:
            logged_user = User(key_name = user.nickname())
            logged_user.put()
            
            self.response.headers['Content-Type'] = 'text/html'
            user_id = user.nickname()

        else:
        
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {}			
			
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))			
			
            
            
class Logout(webapp2.RequestHandler):
    
    def get(self):        
        
        user = users.get_current_user()
        
        if user:
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect(users.create_login_url('/'))
        
        #if user:
         #   self.redirect(users.create_logout_url(self.request.uri))
        #else:
        #self.redirect(users.create_logout_url('/'))


app = webapp2.WSGIApplication([('/',       MainPage),
                               ('/logout', Logout),
                               ('/train',  QueryTrainer)
                               ],
                              debug=True)
							  






