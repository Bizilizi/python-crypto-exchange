import typing as tp

from pydantic import BaseModel


class CreateAccountRequest(BaseModel):
    account_name: str
    btc: float
    eth: float
    usdt: float


class DeleteAccountRequest(BaseModel):
    account_name: str


class CreateSupportedPair(BaseModel):
    symbol_pair: str


class DeleteSupportedPair(BaseModel):
    symbol_pair: str


class CreateOrderRequest(BaseModel):
    account_id: str
    type: str
    amount: float
    price: tp.Optional[float]
    side: str
    symbol_pair: str


class OrderInfoRequest(BaseModel):
    account_id: str
    symbol_pair: str
    order_id: int


class DepthInfoRequest(BaseModel):
    account_id: str
    symbol_pair: str


class AccountInfoRequest(BaseModel):
    account_id: str


class AccountBalanceRequest(BaseModel):
    account_id: str
    symbols: tp.List[str]


class OrderCancelRequest(BaseModel):
    account_id: str
    symbol_pair: str
    order_id: int


class DDoSCheck(BaseModel):
    account_id: str
