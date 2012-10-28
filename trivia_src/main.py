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
import random

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from sets import Set

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

#from webapp2_extras import sessions


from user import *
from query import *


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

def get_current_user_entity():
    
    c_user = User.get( db.Key.from_path('User', users.get_current_user().nickname() ) )
    return c_user
        
def get_user_entity( key_name ):

    c_user = User.get( db.Key.from_path('User', key_name ) )
    return c_user


def user_init( user ):
    
    user = User( key_name = user.nickname() )
    user.put()
            
    return user

def get_number_of_queries():

    Counter = memcache.get("q_no");
    if Counter is None:
        Counter = EntityCounter.get( db.Key.from_path('EntityCounter','Query') )
        if Counter is None:
            return 0
    
    return Counter.counter

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
 
        new_query = Query( key_name = str(q_no), text = question, answer = ans, fake_answers = [] )
        
        category = self.escape("category")
        if category is not None:
            new_query.category = category
        
        tags = self.escape("tags")
        if tags is not None:    
            words = tags.split(';')
            new_query.tags = words
        
        i = 2
        fake_ans = []
        while i <= 4:
            ans = self.escape("answer"+str(i))
            new_query.fake_answers.append( ans )
            i +=1
            
        new_query.put()
        
        c_user = get_current_user_entity()
        c_user.questions.append(str(q_no))
        c_user.put()
    
        self.redirect('/train')

class PlayRandom( webapp2.RequestHandler ):
    
    def get(self):
    
        self.check_user()
        
        query_count = get_number_of_queries()

        q_no = str( random.randint(1,query_count-1) )
        
        print query_count-1
        print q_no
        
        while True:
            fake_q_no = str( random.randint(0,66666) )   # generate random number to obfuscate the q_no
            query = memcache.get("q_" + fake_q_no )
            
            if query is None:
                query = Query.get( db.Key.from_path('Query', q_no ) ) # retrieve the real query
                memcache.set(fake_q_no, query, time = 120 )
                break
        
            
        answers = [ query.answer ] + query.fake_answers
        
        random.shuffle(answers)
            
        template_values = { 'query'   : query.text, 
                            'answers' : answers,
                            'q_id'    : fake_q_no 
                        }
        
        self.response.out.write(str(answers))
        #template = jinja_environment.get_template('random.html')
        #self.response.out.write(template.render(template_values))    
            
    def post(self):
        
        c_user = get_current_user_entity()
        
        if c_user is None:
            return
        
        player_answer = self.escape("answer")
        fake_q_no     = self.escape("q_id")
        
        query = memcache.get( fake_q_no )
        
        if query is None:
            print 'You took too long to answer, error'
        
        if player_answer == query.answer:
            c_user.correct_answers += 1
        else:
            c_user.wrong_answers += 1
        
        
        
    def check_user(self):
        user = users.get_current_user()
        if user is None:
            self.redirect( user.create_login_url(self.request.uri) )

    def escape( self, field ):
        return cgi.escape( self.request.get(field) )

    
class MainPage(webapp2.RequestHandler):
    
    def get(self):
        
        user = users.get_current_user()
        if user:
            logged_user = User(key_name = user.nickname(), correct_answers = 0, wrong_answers = 0, author = user.nickname())
            logged_user.put()
            
            self.response.headers['Content-Type'] = 'text/html'
            user_id = user.nickname()

        else:
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {}			
			
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))			
			
class PlayerStats(webapp2.RequestHandler):
    
    def get(self,usernick):
        
        if usernick == '':
            self.redirect( '/' )
            return
    
        c_user = get_user_entity(usernick)
        
        if usernick == 'me':
            c_user = get_current_user_entity()
        
        if c_user is None:
            self.response.out.write('Unknown user')
            return
        
        self.response.out.write(c_user.author)
        
        self.response.out.write(' correct answers -> ' + str(c_user.correct_answers) )
        self.response.out.write(' wrong answers -> ' + str(c_user.wrong_answers)  )
    
        template_values = {
                           'correct_answers' : c_user.correct_answers,
                           'wrong_answers' : c_user.wrong_answers
                           }
        
        #template = jinja_environment.get_template('index.html')
        #self.response.out.write(template.render(template_values))
        

class Login(webapp2.RequestHandler):
            
    def get(self):
        self.redirect( users.create_login_url('/') )
            
class Logout(webapp2.RequestHandler):
    
    def get(self):        
    
        if users.get_current_user() is not None:
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect(users.create_login_url('/'))
        #if user:
         #   self.redirect(users.create_logout_url(self.request.uri))
        #else:
        #self.redirect(users.create_logout_url('/'))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/logout', Logout),
                               ('/login', Login),
                               ('/train',  QueryTrainer),
                               ('/play/random', PlayRandom),
                               (r'/stats/player/(.*)', PlayerStats)
                               ],
                              debug=True)
							  






