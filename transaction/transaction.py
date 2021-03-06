# -*- coding: utf-8 -*-

from __future__ import print_function
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

from abc import ABCMeta, abstractmethod
try:
    import httplib
except ImportError:
    import http.client as httplib
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
import urllib3
urllib3.disable_warnings()

class TransactionHandler(object):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self):
        """
        Send the order to the brokerage.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedTransaction(object):
    """
    Ticket: contains following data
      ticket ID, units, side, instrument, open time, closed/cancelled time, expiration time,
      open price, closed price, profit, takeProfit, stopLoss, trailingStop, trailingAmount, 
      status (open, closed, pending order, cancelled pending order)
 
    ** for partial close, just create new ID and copy the orginal TicketID.
    Transaction: contains following data
     transaction ID, accound ID, time, type
           MARKET_ORDER_CREATE , STOP_ORDER_CREATE, LIMIT_ORDER_CREATE, MARKET_IF_TOUCHED_ORDER_CREATE,
           ORDER_UPDATE, ORDER_CANCEL, ORDER_FILLED, TRADE_UPDATE, TRADE_CLOSE, MIGRATE_TRADE_OPEN,
           MIGRATE_TRADE_CLOSE, STOP_LOSS_FILLED, TAKE_PROFIT_FILLED, TRAILING_STOP_FILLED, MARGIN_CALL_ENTER,
           MARGIN_CALL_EXIT, MARGIN_CLOSEOUT, SET_MARGIN_RATE, TRANSFER_FUNDS, DAILY_INTEREST, FEE
     instrument, side, units, price, lowerBound, upperBound, takeProfitPrice, stopLossPrice
     trailingStopLossDistance, pl (profit/loss), interst, accountBalance,
     tradeOpened (ticket id, units), tradeReduced (ticket id, units, pl, interest)
    """
    def __init__(self, base_currency):
	self.__TransactionID__ = 0
        self.__Transactions__ = []
	self.__TicketID__ = 0
        self.__Tickets__ = []
        self.__OpenTickets__ = []
        self.base_currency = base_currency        
    def order_open(self, ticker, instrument, units, side, order_type, expiary=None, price=None, lowerBound=None, upperBound=None, stopLoss=0.0, takeProfit=0.0, trailingStop=None, comment=None, magicnumber=None):

        transactiontime = ticker.prices[instrument]['time']
        newTransaction= {"id" : self.__TransactionID__, "instrument" : instrument, "units" : units, "side" : side, "type" : order_type, "expiary" : expiary, "price" : price, "lowerBound" : lowerBound, "upperBound" : upperBound, "stopLoss" : stopLoss, "takeProfit" : takeProfit, "trailingStop" : trailingStop } 

        if side ==  "sell" and order_type == "market":
            price = ticker.prices[instrument]['bid']
        elif side == "buy" and order_type == "market": 
            price = ticker.prices[instrument]['ask']
        else:
            print ("not supported")
            return(False)

        newTicket= {"id" : self.__TicketID__, "instrument" : instrument, "units" : units, "side" : side, "type" : order_type, "time" : transactiontime, "expiary" : expiary, "price" : price, "lowerBound" : lowerBound, "upperBound" : upperBound, "stopLoss" : stopLoss, "takeProfit" : takeProfit, "trailingStop" : trailingStop } 
        self.__Transactions__.append(newTransaction)
        self.__Tickets__.append(newTicket)
        self.__OpenTickets__.append(newTicket)

	self.__TicketID__=self.__TicketID__+1
        self.__TransactionID__=self.__TransactionID__+1
        return(newTicket)


    def order_modify(self, ticketID):
        self.__TransactionID__=self.__TransactionID__+1

    def order_close(self, ticketID):
        self.__TransactionID__=self.__TransactionID__+1

    def get_open_orders(self):
        return (self.__OpenTickets__)
 
#    def order_info(self, ticketID):
                
    
    def orders_stoploss_takeprofit(self, ticker, openorder):
        instrument = openorder['instrument']
        units = openorder['units']
        side = openorder['side']
        price = openorder['price']
        order_type = openorder['type']
        takeProfit = openorder['takeProfit']
        stopLoss = openorder['stopLoss']
	expiary = openorder['expiary']
        lowerBound = openorder['lowerBound']
        upperBound = openorder['upperBound']
        trailingStop = openorder['trailingStop']
        transactiontime = ticker.prices[instrument]['time']

        pnl = Decimal("0")

        quote_currency = instrument[3:]
        if quote_currency == self.base_currency:
            if openorder['side'] == 'buy':
                price = ticker.prices[instrument]['bid']
                if takeProfit == 0.0:
                    takeProfit = 10e+200 #XXX PyFloat_GetMax()             
                if price >= takeProfit:
                    _pnl = ((takeProfit - openorder['price']) * openorder['units'])
                    pips = ((takeProfit - openorder['price']) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    _price = takeProfit
                elif price <= stopLoss:
                    _pnl = - ((openorder['price'] - stopLoss) * openorder['units'])
                    pips = - ((openorder['price'] - stopLoss) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    _price = stopLoss
                else:
                    return(pnl)
            elif openorder['side'] == 'sell':
                price = ticker.prices[instrument]['ask']
                if stopLoss == 0.0:
                    stopLoss = 10e+200 #XXX PyFloat_GetMax()             
                if price <= takeProfit:
                    _pnl = ((openorder['price'] - takeProfit) * openorder['units'])
                    pips = ((openorder['price'] - takeProfit) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    _price = takeProfit
                elif price >= stopLoss:
                    _pnl = - ((stopLoss - openorder['price']) * openorder['units'])
                    pips = - ((stopLoss - openorder['price']) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    _price = stopLoss
                else:
                    return(pnl)
        else:
            quote_currency_pair = "%s%s" % (quote_currency, self.base_currency)
            if openorder['side'] == 'buy':
                price = ticker.prices[instrument]['bid']
                if takeProfit == 0.0:
                    takeProfit = 10e+200 #XXX PyFloat_GetMax()             
                if price >= takeProfit:
                    _pnl = ((takeProfit - openorder['price']) * openorder['units']) * ticker.prices[quote_currency_pair]['bid']
                    pips = ((takeProfit - openorder['price']) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    _price = takeProfit
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                elif price <= stopLoss:
                    _pnl = - ((openorder['price'] - stopLoss) * openorder['units']) * ticker.prices[quote_currency_pair]['bid']
                    pips = - ((openorder['price'] - stopLoss) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    _price = stopLoss
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                else:
                    return(pnl)
            elif openorder['side'] == 'sell':
                price = ticker.prices[instrument]['ask']
                if stopLoss == 0.0:
                    stopLoss = 10e+200 #XXX PyFloat_GetMax()             
                if price <= takeProfit:
                    _pnl = ((openorder['price'] - takeProfit) * openorder['units']) * ticker.prices[quote_currency_pair]['ask']
                    pips = ((openorder['price'] - takeProfit) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    _price = takeProfit
                elif price >= stopLoss:
                    _pnl = - ((stopLoss - openorder['price']) * openorder['units']) * ticker.prices[quote_currency_pair]['ask']
                    pnl = _pnl.quantize(Decimal("0.01"), ROUND_HALF_DOWN)
                    pips = - ((stopLoss - openorder['price']) * 10000).quantize(Decimal("0.1"), ROUND_HALF_DOWN)
                    _price = stopLoss
                else:
                    return(pnl)

        newtradeClosed = {"id" : openorder['id'], "units" : openorder['units'] }
        newTransaction= {"id" : self.__TransactionID__, "instrument" : instrument, "units" : units, "side" : side, "type" : order_type, "expiary" : expiary, "price" : price, "lowerBound" : lowerBound, "upperBound" : upperBound, "stopLoss" : stopLoss, "takeProfit" : takeProfit, "trailingStop" : trailingStop, "tradeClosed" : newtradeClosed } 
        self.__Transactions__.append(newTransaction)
        self.__TransactionID__=self.__TransactionID__+1
        
        opentime = openorder["time"].strftime("%Y-%m-%d %H:%M:%S")
        closetime = ticker.prices[instrument]['time'].strftime("%Y-%m-%d %H:%M:%S")
        duration = ticker.prices[instrument]['time'] - openorder["time"]
        duration_hours, remainder = divmod(duration.seconds, 3600)
        duration_minutes, duration_seconds = divmod(remainder, 60)
        duration_hours += duration.days*24
        print("%s, " % opentime[:23] + "%s, " % closetime[:23] + "%6s, " % openorder["instrument"] + "%4s, " 
         % openorder["side"] + "%7s, " % openorder["price"] + "%7s, " % _price + "%6s, " % pips 
         + "pips, %8s" % pnl + "$, " + "%02d:%02d, " % (duration_hours, duration_minutes)
         + "%7s, " % ticker.prices[instrument]['bid'] + "%7s" % ticker.prices[instrument]['ask'])
        # remove ticket
        self.__Tickets__.remove(openorder)
        self.__OpenTickets__.remove(openorder)
        
        return (pnl)


class OANDATransactionHandler(TransactionHandler):
    def __init__(self, domain, access_token, account_id):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.conn = self.obtain_connection()

    def obtain_connection(self):
        return httplib.HTTPSConnection(self.domain)

    def execute_order(self, event):
        instrument = "%s_%s" % (event.instrument[:3], event.instrument[3:])
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer " + self.access_token
        }
        params = urlencode({
            "instrument" : instrument,
            "units" : event.units,
            "type" : event.order_type,
            "side" : event.side
        })
        self.conn.request(
            "POST", 
            "/v1/accounts/%s/orders" % str(self.account_id), 
            params, headers
        )
        response = self.conn.getresponse().read()
        print(response)
        
