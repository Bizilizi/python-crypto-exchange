import typing as t
from collections import defaultdict
from datetime import datetime
from functools import wraps

from aiohttp import web
from exchange.core.errors import (
    InsufficientFunds,
    OrderCancellationError,
    OrderCreationError,
    OrderNotFound,
    PairAlreadyExisted,
    PairDeletionError,
    TooSmallOrderAmount,
    UnsupportedPairs,
    WrongCredentials,
    WrongOrderID,
)
from pydantic import ValidationError

from . import schema


# Status Pages middleware

_Handler = t.Callable[[web.Request], t.Awaitable[web.StreamResponse]]


@web.middleware
async def status_pages(request: web.Request, handler: _Handler) -> web.StreamResponse:
    try:
        return await handler(request)
    except ValidationError as e:
        return error(488, e.json())
    except UnsupportedPairs:
        return error(455, "Unsupported pairs error. Invalid pair format specified")
    except WrongCredentials:
        return error(401, "Unauthorized Error. Account with such name is not existed")
    except WrongOrderID:
        return error(456, "Wrong order id")
    except TooSmallOrderAmount:
        return error(457, "Too small order amount error")
    except InsufficientFunds:
        return error(476, "Insufficient funds error. Not enough funds")
    except OrderCreationError:
        return error(462, "Order creation error. Unable to create order")
    except PairAlreadyExisted:
        return error(486, "Can not create new pair, because it is already existed.")
    except PairDeletionError:
        return error(487, "Can not delete pair.")
    except OrderNotFound:
        return error(477, "Order was not found")
    except OrderCancellationError:
        return error(463, "Order cancellation error. Unable to close order")
    except Exception as e:
        return error(500, str(e.args))


class DDoS:
    # DDoS decorator by value of account argument in json
    # This simple decorator checks whether RPS was exceeded or not

    _request_count: int
    _time_limit: int

    def __init__(self, request_count: int, time_limit: int) -> None:
        self._request_count = request_count
        self._time_limit = time_limit

    def __call__(
        self, func: t.Callable[[web.Request], t.Awaitable[web.Response]]
    ) -> t.Callable[[web.Request], t.Awaitable[web.Response]]:
        request_dict: t.Dict[str, t.List[datetime]] = defaultdict(list)

        @wraps(func)
        async def wrapped(request: web.Request) -> web.Response:
            json_data = schema.DDoSCheck.parse_obj(await request.json())
            key_value = json_data.account_name

            request_dict[key_value].append(datetime.now())
            request_history = request_dict[key_value]

            if len(request_history) >= self._request_count:
                if (
                    request_history[self._request_count - 1] - request_history[0]
                ).seconds < self._time_limit:
                    request_history.pop(0)
                    return error(429, "DDoS protection error. Too Many Requests")
                request_history.pop(0)

            return await func(request)

        return wrapped


def error(error_code: int, custom_message: t.Optional[str] = None) -> web.Response:
    message = custom_message or ""
    return web.json_response(
        {"success": False, "error_code": error_code, "message": message}
    )


def success(result: t.Dict[str, t.Any]) -> web.Response:
    return web.json_response({"success": True, "result": result})
