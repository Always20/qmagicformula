# -*- coding: utf-8 -*-


from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class ExchangeRate(db.Model):
    hkd = db.StringProperty()
    usd = db.StringProperty()
    

def get():
    entry = memcache.get('exchange_rate')
    if entry is None:
        entry = ExchangeRate.get_or_insert('exchange_rate')
        memcache.add('exchange_rate', entry)
    return entry


def put(entry):
    entry.put()
    memcache.set('exchange_rate', entry)
    
    
class UpdateExchangeRateHandler(webapp.RequestHandler):
    
    def __get_exchange_rate(self, area):
        url = "http://download.finance.yahoo.com/d/quotes.html?s=%sCNY=X&f=l1" % area
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            return result.content.strip()
            
    def get(self):
        usd = self.__get_exchange_rate('USD')
        hkd = self.__get_exchange_rate('HKD')
        entry = get()
        entry.usd = usd
        entry.hkd = hkd
        put(entry)
            
        
application = webapp.WSGIApplication([('/tasks/updateexchangerate', UpdateExchangeRateHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()