# Python exchange core

Pure python, Binance like exchange that makes model testing easier.  
Dockerized for the convenience. 
https://hub.docker.com/repository/docker/ewriji/python-crypto-exchange


# Rest API 
---

## Admin Endpoints

## Account Creation
This endpoint creates account instance in exchange. Requires Name of account which behaves like credential for order creation requests.

### Request 
> **URL** : `/account/create`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description           | Type            |
|--------------|-----------------------|-----------------|
| account_name | Unique account name   | String          |
| balances     | Json of init balances | Dict[str,float] |
  
**Json example** :
```json
{
"account_name": "Bernini",
"balances":{"btc": 10, "eth": 15, "usdt": 200}
}
```

## Account Deletion
This endpoint deletes exsited account from exchange.

### Request 
> **URL** : `/account/delete`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description           | Type            |
|--------------|-----------------------|-----------------|
| account_name | Unique account name   | String          |
  
**Json example** :
```json
{
"account_name": "Bernini"
}
```

## Get all accounts
This endpoint returns list of existed accounts.

### Request 
> **URL** : `/account/get_all`
> 
> **Method** : `GET`

## Create symbol pair
This endpoint register new symbol pair in exhange. After registration accounts are allowed to trade on this pair.

### Request 
> **URL** : `/pair/create`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description                  | Type            |
|--------------|------------------------------|-----------------|
| symbol_pair  | Unique name of symbol pair   | String          |

**Json example** :
```json
{
"symbol_pair": "BTC/ETH"
}
```

## Delete symbol pair
This endpoint delete symbol pair from exhange.

### Request 
> **URL** : `/pair/delete`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description                  | Type            |
|--------------|------------------------------|-----------------|
| symbol_pair  | Unique name of symbol pair   | String          |

**Json example** :
```json
{
"symbol_pair": "BTC/ETH"
}
```

## Get all registered symbol pairs
This endpoint returns list of registered symbol pairs.

### Request 
> **URL** : `/pair/get_all`
> 
> **Method** : `GET`

---

## Exchange endpoints

## Order creation
This endpoint creates order by given account name and symbol pair.

### Request 
> **URL** : `/order/create`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description                            | Type   |
|--------------|----------------------------------------|--------|
| account_name | Unique account name                    | String |
| type         | Order type Limit/Market                | String |
| amount       | Order amount                           | float  |
| price        | Order price. Optional for market order | float  |
| side         | Order side Sell/Buy                    | String |
| symbol_pair  | Order symbol pair                      | String |

## Order cancelation
This endpoint cancel pushed order.

### Request 
> **URL** : `/order/cancel`
> 
> **Method** : `POST`
#### Json Format :
| Field        | Description                            | Type   |
|--------------|----------------------------------------|--------|
| account_name | Unique account name                    | String |
| order_id     | Order id.                              | Int    |
| symbol_pair  | Order symbol pair                      | String |

## Order info
This endpoint returns order information by given id.

### Request 
> **URL** : `/order`
> 
> **Method** : `GET`
#### Json Format :
| Field        | Description                            | Type   |
|--------------|----------------------------------------|--------|
| account_name | Unique account name                    | String |
| order_id     | Order id.                              | Int    |
| symbol_pair  | Order symbol pair                      | String |


## Deph
This endpoint returns order book information by given symbol pair

### Request 
> **URL** : `/depth`
> 
> **Method** : `GET`
#### Json Format :
| Field        | Description                            | Type   |
|--------------|----------------------------------------|--------|
| account_name | Unique account name                    | String |
| symbol_pair  | Order symbol pair                      | String |


## Account balance
This endpoint returns balance of account.

### Request 
> **URL** : `/account/balance`
> 
> **Method** : `GET`
#### Json Format :
| Field        | Description                            | Type         |
|--------------|----------------------------------------|--------------|
| account_name | Unique account name                    | String       |
| symbols      | List of requested symbols              | List[String] |

