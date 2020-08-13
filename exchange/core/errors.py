class OrderCreationError(Exception):
    pass


class OrderCancellationError(Exception):
    pass


class ZeroSpreadError(Exception):
    pass


class WrongCredentials(Exception):
    pass


class UnsupportedPairs(Exception):
    pass


class WrongOrderID(Exception):
    pass


class WrongSymbol(Exception):
    pass


class FeesCollectError(Exception):
    pass


class TooSmallOrderAmount(Exception):
    pass


class OtherException(Exception):
    pass


class ExchangeError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class InsufficientFunds(Exception):
    pass


class NetworkError(Exception):
    pass


class BadRequest(Exception):
    pass


class InvalidOrder(Exception):
    pass


class OrderNotFound(Exception):
    pass


class DDoSProtection(Exception):
    pass


class ExchangeNotAvailable(Exception):
    pass


class InvalidNonce(Exception):
    pass


class RequestTimeout(Exception):
    pass


class RequestError(Exception):
    pass


class ActiveMarket(Exception):
    pass


class CloudFlareError(Exception):
    pass


class OrderConfirmationTimeout(Exception):
    pass


class TooManyRequests(Exception):
    pass


class PairAlreadyExisted(Exception):
    pass


class PairDeletionError(Exception):
    pass


class IncorrectPrice(Exception):
    pass


class AgentError(Exception):
    pass
