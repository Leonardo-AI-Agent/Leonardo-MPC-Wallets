#!/usr/bin/env python3
"""
Module: client.py

This module implements the CDPAgentkitClient to manage MPC wallets and related operations.
Reference: https://coinbase.github.io/cdp-sdk-python/cdp.html
"""

import json
import os
from typing import Dict, Any, Optional
from loguru import logger
from cdp import Cdp, Wallet

# ✅ Configure Loguru Logging
logger.add("logs/cdp_transactions.log", rotation="500 MB", level="DEBUG", backtrace=True, diagnose=True)

class CDPAgentkitClient:
    """
    Client for interacting with the CDP SDK to manage MPC wallets securely.
    """

    def __init__(self, api_key_name: str, api_key_private: str) -> None:
        """
        Initialize the CDPAgentkitClient with API credentials.
        
        :param api_key_name: The API key ID (public identifier).
        :param api_key_private: The API key secret (used for authentication).
        """
        self.api_key_name = api_key_name
        self.api_key_private = api_key_private
        self.seed_storage_path = "my_wallet_seed.json"  # Define wallet seed storage file

        # Initialize CDP SDK
        logger.info("Configuring CDP SDK with API credentials...")
        Cdp.configure(self.api_key_name, self.api_key_private)
        logger.success("CDP SDK configured successfully.")

    def create_wallet(self, network_id: str) -> Dict[str, Any]:
        """
        Create a new MPC wallet on the specified network and generate an address.
        
        :param network_id: The blockchain network identifier (e.g., 'base-sepolia').
        :return: A dict with wallet details and the generated address.
        :raises Exception: On failure.
        """
        try:
            logger.info("Creating MPC wallet on network: {}", network_id)
            wallet = Wallet.create(network_id=network_id)
            logger.info("Generating address for wallet ID: {}", wallet.id)
            wallet_address = wallet.create_address()
            address_data = {
                "address_id": wallet_address.address_id,
                "wallet_id": wallet.id,
                "network_id": wallet.network_id
            }
            wallet.save_seed(self.seed_storage_path, encrypt=True)
            logger.success("Seed for wallet {} saved securely to {}.", wallet.id, self.seed_storage_path)
            wallet_data = {
                "wallet_id": wallet.id,
                "network_id": wallet.network_id,
                "address": address_data
            }
            logger.success("Wallet and address created successfully: {}", wallet_data)
            return wallet_data
        except Exception as e:
            logger.error("Failed to create wallet and address: {}", e, exc_info=True)
            raise Exception(f"Failed to create wallet and address: {str(e)}")
    
    def import_wallet(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import an existing MPC wallet by saving the provided encrypted seed.
        This allows the wallet to be rehydrated for subsequent operations.
        
        Expected import_data JSON format:
        {
        "encrypted_seed": "<your encrypted seed string>"
        }
        
        :param import_data: A dictionary containing the encrypted seed.
        :return: A dictionary containing the wallet details after loading it.
        :raises Exception: If wallet import fails.
        """
        try:
            if "encrypted_seed" not in import_data:
                raise Exception("Missing 'encrypted_seed' in payload.")
            encrypted_seed = import_data["encrypted_seed"]

            # Write the encrypted seed to the seed storage file.
            with open(self.seed_storage_path, "w") as f:
                f.write(encrypted_seed)
            logger.success("Encrypted wallet seed saved to {}.", self.seed_storage_path)

            # Load the wallet from the saved encrypted seed.
            wallet = self.load_wallet()
            if not wallet:
                raise Exception("Failed to load wallet after saving seed.")
            imported_wallet = wallet.export_data()
            logger.success("Wallet imported successfully: {}", imported_wallet)
            return imported_wallet

        except Exception as e:
            logger.error("Failed to import wallet: {}", e, exc_info=True)
            raise Exception(f"Failed to import wallet: {str(e)}")


    def load_wallet(self) -> Optional[Wallet]:
        """
        Load the wallet from the locally stored encrypted seed.

        :return: Wallet instance if successfully loaded, otherwise None.
        :raises Exception: If wallet loading fails.
        """
        try:
            if not os.path.exists(self.seed_storage_path):
                raise Exception("Wallet seed file not found.")

            logger.info("Loading wallet from saved encrypted seed...")

            # Load wallet using the saved file path
            wallet = Wallet.load_seed(file_path=self.seed_storage_path, passphrase=self.api_key_private)

            logger.success("Wallet successfully loaded: {}", wallet.id)
            return wallet

        except Exception as e:
            logger.error("Failed to load wallet: {}", e, exc_info=True)
            raise Exception(f"Failed to load wallet: {str(e)}")




    def create_address(self) -> Dict[str, Any]:
        """
        Create a new address for the locally stored MPC wallet.
        
        :return: A dict containing the new address details.
        :raises Exception: On failure.
        """
        try:
            logger.info("Loading wallet for new address creation...")
            wallet = self.load_wallet()
            if not wallet:
                raise Exception("No wallet found to create a new address.")
            logger.info("Generating new address for wallet ID: {}", wallet.id)
            new_address = wallet.create_address()
            address_data = {
                "address_id": new_address.address_id,
                "wallet_id": wallet.id,
                "network_id": wallet.network_id
            }
            logger.success("New address created successfully: {}", address_data)
            return address_data
        except Exception as e:
            logger.error("Failed to create new address: {}", e, exc_info=True)
            raise Exception(f"Failed to create new address: {str(e)}")

    def export_wallet(self) -> Dict[str, Any]:
        """
        Export the data of the locally stored MPC wallet.
        
        :return: A dict containing the exported wallet data.
        :raises Exception: On failure.
        """
        try:
            wallet = self.load_wallet()
            if not wallet:
                raise Exception("No wallet found to export.")
            exported_wallet = wallet.export_data()
            logger.success("Wallet exported successfully: {}", exported_wallet)
            return exported_wallet
        except Exception as e:
            logger.error("Failed to export wallet: {}", e, exc_info=True)
            raise Exception(f"Failed to export wallet: {str(e)}")

    def retrieve_balances(self) -> Dict[str, Any]:
        """
        Retrieve the balances of assets held in the locally stored wallet.
        
        :return: A dict containing asset balances.
        :raises Exception: On failure.
        """
        try:
            wallet = self.load_wallet()
            if not wallet:
                raise Exception("No wallet found to retrieve balances.")
            balances = wallet.balances()
            logger.success("Balances retrieved successfully: {}", balances)
            return balances
        except Exception as e:
            logger.error("Failed to retrieve balances: {}", e, exc_info=True)
            raise Exception(f"Failed to retrieve balances: {str(e)}")

    def create_webhook(self, callback_url: str) -> Dict[str, Any]:
        """
        Set up a webhook to receive notifications for transactions related to the stored wallet.
        
        :param callback_url: The URL to receive webhook notifications.
        :return: A dict confirming webhook setup.
        :raises Exception: On failure.
        """
        try:
            wallet = self.load_wallet()
            if not wallet:
                raise Exception("No wallet found to create webhook.")
            logger.info("Creating webhook for wallet ID: {}", wallet.id)
            webhook = Wallet.create_webhook(wallet.id, callback_url, event_types=["TRANSACTION_RECEIVED"])
            logger.success("Webhook created successfully: {}", webhook)
            return webhook
        except Exception as e:
            logger.error("Failed to create webhook: {}", e, exc_info=True)
            raise Exception(f"Failed to create webhook: {str(e)}")

    def execute_gasless_transaction(self, wallet_id: str, to_address: str, amount: str, asset: str = "USDC") -> Dict[str, Any]:
        """
        Execute a gasless transaction from the specified wallet.
        By default, the asset is USDC.
        
        :param wallet_id: The sender's wallet ID.
        :param to_address: The recipient's blockchain address.
        :param amount: The amount to send (in smallest unit).
        :param asset: The asset to transfer (default "USDC").
        :return: A dict containing the transfer details.
        :raises Exception: On failure.
        """
        request_path = "/v2/transfers"
        url = Cdp.get_api_base() + request_path  # Assume Cdp.get_api_base() returns the base URL.
        payload = {
            "wallet_id": wallet_id,
            "to": to_address,
            "amount": amount,
            "asset": asset,
            "transfer_type": "GASLESS"
        }
        body = json.dumps(payload)
        headers = self._get_headers("POST", request_path, body)
        try:
            logger.info("Executing gasless transaction with payload: {}", payload)
            response = Cdp.request("POST", request_path, data=body, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            tx_data = response.json()
            logger.success("Gasless transaction executed successfully: {}", tx_data)
            return tx_data
        except Exception as e:
            logger.error("Failed to execute gasless transaction: {}", e, exc_info=True)
            raise Exception(f"Failed to execute gasless transaction: {str(e)}")
