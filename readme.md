# Python exchange core

Pure python, Binance like exchange that makes model testing easier.  
Dockerized for the convenience. 
https://hub.docker.com/repository/docker/ewriji/python-crypto-exchange

# Documentation 

Checkout [wiki](https://github.com/Bizilizi/python-crypto-exchange/wiki/Api-documentation) for API documentation.


# Structure

Some common structures needed for exchange operation can be found in `exchange.core.entites` package.  

Matching model `exchange.core.match_model.py` is fully asynchrounous wich allows to concurrently perform match operation for several symbol pairs. After each invocation of both `market_match`, `limit_match`, MatchModel returns list of reports fully describing process if matching maker orders by taker order. Those report used for balance recalculation, event emitting and in the nearest future for statistics calculation.

Exchange instance `exchange.core.exchange.py` is responsible for the coroutine sinchronization and also processing administrative (Account management, Symbol Pair management) and exchange requests (Creating/Canceling Orders). Since the match model is asynchronous, entities like `OrderBook` and `Account` required grant access to their data. Which can be implemented through async context manager.
Before the order can be sent to match model, exchange perform: additional checks to cover error cases, froze necessary amount of balance and then push order to match model. After each pushing of order to match model, exchange perform reports processing, in order to recalculate balances and emit events.
