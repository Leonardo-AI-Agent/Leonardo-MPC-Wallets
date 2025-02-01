from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import time
from loguru import logger

# Import configuration and client
from config import API_KEY_NAME, API_KEY_PRIVATE  # Ensure these are defined in your config.py
from mpc_wallet_service.client import CDPAgentkitClient

# Initialize FastAPI app
app = FastAPI(title="MPC Wallet Management API", version="1.0")

# Initialize the CDP API Client
cdp_client = CDPAgentkitClient(API_KEY_NAME, API_KEY_PRIVATE)

# ------------------------------------------------------------------------------
# Middleware for Logging & Performance Analytics
# ------------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request: {} {}", request.method, request.url)
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info("Completed {} {} in {:.4f} seconds", request.method, request.url, process_time)
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ------------------------------------------------------------------------------
# Pydantic Models for Request Bodies
# ------------------------------------------------------------------------------
class ImportWalletRequest(BaseModel):
    wallet_data: Dict[str, Any]

class WebhookRequest(BaseModel):
    callback_url: str

class GaslessTransactionRequest(BaseModel):
    wallet_id: str
    to_address: str
    amount: str
    asset: Optional[str] = "USDC"

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.post("/wallet/create", response_model=Dict[str, Any])
async def create_wallet(network_id: str):
    """
    Create a new MPC wallet on the specified network.
    Query Parameter:
      - network_id: e.g., 'base-sepolia'
    
    This endpoint creates a wallet, saves its encrypted seed locally, and returns wallet details.
    """
    try:
        wallet_data = cdp_client.create_wallet(network_id)
        logger.success("Created wallet: {}", wallet_data)
        return wallet_data
    except Exception as e:
        logger.error("Create wallet error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


from fastapi import HTTPException, Request

@app.post("/wallet/import", response_model=Dict[str, Any])
async def import_wallet(request: Request):
    """
    Import an existing MPC wallet using its encrypted seed data (as a string).
    """
    try:
        # Parse the incoming JSON request body
        body = await request.json()

        # Ensure the 'encrypted_seed' field is in the request payload
        if "encrypted_seed" not in body:
            raise HTTPException(status_code=422, detail="Missing 'encrypted_seed' field in payload")
        
        # Get the encrypted seed (string)
        encrypted_seed = body["encrypted_seed"]

        # Save the encrypted seed string to a file
        seed_file_path = "my_wallet_seed.json"
        with open(seed_file_path, 'w') as f:
            f.write(encrypted_seed)

        # Now, load the wallet using the saved file
        imported_wallet = cdp_client.load_wallet()  # This loads the wallet from the file path
        logger.success("Imported wallet: {}", imported_wallet)

        return imported_wallet

    except Exception as e:
        logger.error("Import wallet error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))



@app.get("/wallet/export", response_model=Dict[str, Any])
async def export_wallet():
    """
    Export the data of the locally stored MPC wallet.
    The wallet is rehydrated by loading its encrypted seed.
    """
    try:
        exported_wallet = cdp_client.export_wallet()
        logger.success("Exported wallet: {}", exported_wallet)
        return exported_wallet
    except Exception as e:
        logger.error("Export wallet error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/wallet/balances", response_model=Dict[str, Any])
async def retrieve_balances():
    """
    Retrieve the asset balances of the locally stored MPC wallet.
    The wallet is rehydrated via its encrypted seed.
    """
    try:
        balances = cdp_client.retrieve_balances()
        logger.success("Retrieved balances: {}", balances)
        return balances
    except Exception as e:
        logger.error("Retrieve balances error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/wallet/address", response_model=Dict[str, Any])
async def create_address():
    """
    Create a new address for the locally stored MPC wallet.
    The wallet is loaded from its encrypted seed.
    """
    try:
        new_address = cdp_client.create_address()
        logger.success("Created new address: {}", new_address)
        return new_address
    except Exception as e:
        logger.error("Create address error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/transaction/gasless", response_model=Dict[str, Any])
async def execute_gasless_transaction(tx_request: GaslessTransactionRequest):
    """
    Execute a gasless transaction from the specified wallet.
    Request Body:
      - wallet_id: Sender's wallet ID
      - to_address: Recipient address
      - amount: Amount to send (smallest unit)
      - asset: Asset to transfer (default is USDC)
    """
    try:
        tx_response = cdp_client.execute_gasless_transaction(
            tx_request.wallet_id,
            tx_request.to_address,
            tx_request.amount,
            tx_request.asset
        )
        logger.success("Executed gasless transaction: {}", tx_response)
        return tx_response
    except Exception as e:
        logger.error("Gasless transaction error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/wallet/webhook", response_model=Dict[str, Any])
async def create_webhook(webhook_request: WebhookRequest):
    """
    Set up a webhook to receive notifications for incoming transactions.
    Request Body:
      - callback_url: URL to receive webhook notifications.
    """
    try:
        webhook_response = cdp_client.create_webhook(webhook_request.callback_url)
        logger.success("Created webhook: {}", webhook_response)
        return webhook_response
    except Exception as e:
        logger.error("Create webhook error: {}", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
