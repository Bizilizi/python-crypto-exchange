import typing as t

from pydantic import BaseModel


class CreateAccountRequest(BaseModel):
    account_name: str
    balances: t.Dict[str, float]


class DeleteAccountRequest(BaseModel):
    account_name: str


class CreateSupportedPair(BaseModel):
    symbol_pair: str


class DeleteSupportedPair(BaseModel):
    symbol_pair: str


class CreateOrderRequest(BaseModel):
    account_name: str
    type: str
    amount: float
    price: t.Optional[float]
    side: str
    symbol_pair: str


class OrderInfoRequest(BaseModel):
    account_name: str
    symbol_pair: str
    order_id: int


class DepthInfoRequest(BaseModel):
    account_name: str
    symbol_pair: str


class AccountInfoRequest(BaseModel):
    account_name: str


class AccountBalanceRequest(BaseModel):
    account_name: str
    symbols: t.List[str]


class OrderCancelRequest(BaseModel):
    account_name: str
    symbol_pair: str
    order_id: int


class DDoSCheck(BaseModel):
    account_name: str
