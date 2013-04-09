# -*- coding: utf-8 -*-


import datetime
import logging
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import stock
    
    
class ShowStockInfoHandler(webapp.RequestHandler):
    
    def __filter(self, stocks):
        content = []
        results = []
        miss = []
        p = 0.0
        b = 0.0
        e = 0.0
        for s in stocks:
            if s.market_capital == 0.0:
                content.append("The market capital is 0 for %s %s\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.earnings_date is None:
                content.append("There is no earnings for %s %s\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if datetime.date.today().year - s.earnings_date.year > 2:
                content.append("The earnings is too old for %s %s %s\n" % (s.ticker, s.title, s.earnings_date.strftime("%Y%m%d")))
                miss.append(s.ticker)
                continue
            p += s.market_capital
            b += s.ownership_interest
            e += s.net_profit
            if s.bank_flag == True:
                content.append("The stock (%s, %s) is a bank\n" % (s.ticker, s.title))
                miss.append(s.ticker)
                continue
            if s.market_capital_date != datetime.date.today():
                content.append("The stock (%s, %s) is not in Google List\n" % (s.ticker, s.title))
            sv = stock.StockView()
            try:
                sv.parse(s)
            except Exception as e:
                content.append("Parse stock (%s, %s) has %s\n" % (s.ticker, s.title, e))
                continue
            results.append(sv)
        return (results, content, miss, p/b, p/e)
            
    
    def __magicformula(self, stocks):
        results, content, miss, pb, pe = self.__filter(stocks)
        results = sorted(results, cmp=lambda a, b : stock.cmp_roic(a, b))
        content.append("Total: %s, Sorted: %s Miss: %s" % (len(stocks), len(results), len(miss)))
        mail.send_mail(sender="prstcsnpr@gmail.com",
                       to="prstcsnpr@gmail.com",
                       subject="神奇公式执行结果",
                       body=''.join(content))
        for i in range(len(results)):
            if i != 0 and stock.cmp_roic(results[i], results[i-1]) == 0:
                results[i].roic_rank = results[i-1].roic_rank
            else:
                results[i].roic_rank = i + 1
        results = sorted(results, cmp=lambda a, b : stock.cmp_ebit_ev(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_ebit_ev(results[i], results[i-1]) == 0:
                results[i].ebit_ev_rank = results[i-1].ebit_ev_rank
            else:
                results[i].ebit_ev_rank = i + 1
        results = sorted(results, key=lambda stock : stock.roic_rank + stock.ebit_ev_rank)
        for i in range(len(results)):
            if i != 0 and results[i].roic_rank + results[i].ebit_ev_rank == results[i-1].roic_rank + results[i-1].ebit_ev_rank:
                results[i].rank = results[i-1].rank
            else:
                results[i].rank = i + 1
            results[i].format()
        return pb, pe, results
    
    def __send_mail(self, content):
        receiver="magicformula@googlegroups.com"
        mail.send_mail(sender="prstcsnpr@gmail.com",
                       to=receiver,
                       subject="神奇公式",
                       body='',
                       html=content)
        logging.info('Mail result for magicformula to %s' % (receiver))
            
    def get(self):
        values = {}
        query = db.Query(stock.Stock)
        stocks = query.fetch(10000)
        pb, pe, stocks = self.__magicformula(stocks)
        position=50
        while position<len(stocks):
            if stocks[position].rank == stocks[position - 1].rank:
                position = position + 1
            else:
                break
        values['stocks'] = stocks[0 : position]
        values['PB'] = "%.4f" % (pb)
        values['PE'] = "%.2f" % (pe)
        content = template.render('qmagicformula.html', values)
        self.response.write(content)
        self.__send_mail(content)
        
            
        
application = webapp.WSGIApplication([('/tasks/showstockinfo', ShowStockInfoHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()