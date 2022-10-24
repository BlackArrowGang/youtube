from http.client import HTTPException
from fastapi import FastAPI
from ftx_client import FtxClient
from pydantic import BaseModel

app = FastAPI()

ftxClient = FtxClient('tradingBot')

class TradingViewAlert(BaseModel):
    dry_run: bool = False
    symbol: str
    position_side: str
    timenow: str
    close: float

def usd_to_coins(total_usd: float, price: float, risk: float = 0.2):
    """
    Based on the size of the risk, returns
    the amount of coins you can buy with the
    total usd.
    """
    risk_usd: float = total_usd * risk
    coins_total: float = risk_usd / price
    return coins_total

@app.post("/webhook/buy")
def buy(tradingViewAlert: TradingViewAlert):
    if tradingViewAlert.position_side != 'buy':
        raise HTTPException(status_code=400, detail="The order must be buy")
    market = tradingViewAlert.symbol
    side = tradingViewAlert.position_side
    price = tradingViewAlert.close
    total_usd = ftxClient.get_total_usd_balance()
    coins = usd_to_coins(total_usd, price)
    print("market: "+market+"\n"+
          "side: "+side+"\n"+
          "price: "+str(price)+"\n"+
          "total_usd: "+str(total_usd)+"\n"+
          "coins: "+str(coins))
    if tradingViewAlert.dry_run:
        print("Do Nothing. Dry Run.")
        result = None
    else:
        result = ftxClient.place_order(market, side, price, coins)
    return result
