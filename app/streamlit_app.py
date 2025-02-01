#!/usr/bin/env python3
"""
Streamlit App: streamlit_app.py

This app provides a UI to test the MPC wallet management & transaction signing service using the CDP SDK.
"""

import sys
import os
import json
import streamlit as st
from loguru import logger
import importlib.util
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.let_it_rain import rain


# ✅ Configure Loguru Logger
logger.add("logs/streamlit_debug.log", rotation="500 MB", level="DEBUG", backtrace=True, diagnose=True)

# ✅ Add project root to sys.path to allow importing from root modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ✅ Dynamically Load config.py from Project Root
config_path = os.path.abspath(os.path.join(project_root, "config.py"))
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# ✅ Import the necessary components from the CDP SDK
from mpc_wallet_service.client import CDPAgentkitClient  # ✅ Corrected Import Path

# ✅ Retrieve configuration values from config.py
API_KEY_NAME = config.API_KEY_NAME
API_KEY_PRIVATE = config.API_KEY_PRIVATE

# ✅ Initialize the CDP API Client
cdp_client = CDPAgentkitClient(API_KEY_NAME, API_KEY_PRIVATE)

# ✅ Streamlit UI - Fancy Layout
st.set_page_config(page_title="MPC Wallet Management", page_icon="💳", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🔹 MPC Wallet Management Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Powered by Coinbase CDP SDK</h4>", unsafe_allow_html=True)

st.divider()  # Adds a visual separator

### **🔹 Section 1: Create an MPC Wallet**
with st.container():
    st.markdown("## 💰 Create an MPC Wallet")

    network_id = st.text_input("🔹 Enter Network ID (e.g., `base-sepolia`)", value="base-sepolia")

    if st.button("🚀 Create Wallet", use_container_width=True):
        try:
            wallet_data = cdp_client.create_wallet(network_id)
            st.session_state.wallet_data = wallet_data

            # ✅ Extract wallet details
            wallet_id = wallet_data.get("wallet_id", "⚠️ Not Available")
            network_id = wallet_data.get("network_id", "⚠️ Not Available")
            wallet_address = wallet_data["address"]["address_id"] if "address" in wallet_data else "⚠️ Not Available"

            st.success("✅ Wallet Created Successfully!")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="🔹 Wallet ID", value=wallet_id)
                st.metric(label="📡 Network ID", value=network_id)

            with col2:
                st.metric(label="🏦 Wallet Address", value=wallet_address)

            # ✅ Apply Stylish Metric Cards
            style_metric_cards(
                background_color="#f0f2f6",
                border_size_px=1,
                border_color="#e0e0e0",
                border_radius_px=8,
                border_left_color="#1f77b4",
                box_shadow=True
            )
            
            rain(
                emoji="🎈",
                font_size=54,
                falling_speed=5,
                animation_length="infinite",
            )

            logger.success("Wallet created successfully! Details: {}", wallet_data)

        except Exception as e:
            st.error(f"❌ Failed to create wallet: {e}")
            logger.error("Wallet creation failed: {}", e, exc_info=True)


### **🔹 Section 2: Export Wallet**
with st.container():
    st.markdown("## 📤 Export Wallet")
    
    if "wallet_data" in st.session_state:
        export_wallet_id = st.session_state.wallet_data.get("wallet_id", "⚠️ Not Available")
    else:
        export_wallet_id = st.text_input("🔹 Enter Wallet ID to Export")

    if st.button("📜 Export Wallet Data", use_container_width=True):
        try:
            exported_wallet = cdp_client.export_wallet()
            st.success("✅ Wallet Exported Successfully!")

            with st.expander("📜 Exported Wallet Data", expanded=True):
                st.json(exported_wallet)

            logger.success("Wallet exported successfully! Details: {}", exported_wallet)
        except Exception as e:
            st.error(f"❌ Failed to export wallet: {e}")
            logger.error("Wallet export failed: {}", e, exc_info=True)


### **🔹 Section 3: Retrieve Wallet Balances**
with st.container():
    st.markdown("## 💰 Retrieve Wallet Balances")

    if "wallet_data" in st.session_state:
        balance_wallet_id = st.session_state.wallet_data.get("wallet_id", "⚠️ Not Available")
    else:
        balance_wallet_id = st.text_input("🔹 Enter Wallet ID to Retrieve Balances")

    if st.button("💵 Retrieve Balances", use_container_width=True):
        try:
            balances = cdp_client.retrieve_balances()
            st.success("✅ Balances Retrieved Successfully!")

            with st.expander("📜 Wallet Balances", expanded=True):
                st.json(balances)

            logger.success("Wallet balances retrieved successfully! Details: {}", balances)
        except Exception as e:
            st.error(f"❌ Failed to retrieve balances: {e}")
            logger.error("Balance retrieval failed: {}", e, exc_info=True)


### **🔹 Section 4: Setup Webhook for Incoming Transactions**
if "wallet_data" in st.session_state:
    with st.container():
        st.markdown("## 🔔 Webhook Setup for Incoming Transactions")

        wallet_id = st.session_state.wallet_data.get("wallet_id", "⚠️ Not Available")
        callback_url = st.text_input("🔹 Enter Webhook Callback URL", value="https://your-server.com/webhook")

        if st.button("🔔 Setup Webhook", use_container_width=True):
            try:
                webhook_response = cdp_client.create_webhook(callback_url)
                st.success("✅ Webhook Setup Successfully!")

                with st.expander("📜 Webhook Details", expanded=False):
                    st.json(webhook_response)

                logger.success("Webhook setup successfully! Details: {}", webhook_response)

            except Exception as e:
                st.error(f"❌ Failed to setup webhook: {e}")
                logger.error("Webhook setup failed: {}", e, exc_info=True)

### **New Section: Create a New Wallet Address**
if "wallet_data" in st.session_state:
    with st.container():
        st.markdown("## 🔹 Create a New Wallet Address")
        if st.button("✨ Create New Address", use_container_width=True):
            try:
                new_address_data = cdp_client.create_address()
                st.success("✅ New address created successfully!")
                st.json(new_address_data)
                
                # Optionally, update the stored wallet data to include the new address.
                # Here, if the existing "address" is a dict, we convert it into a list and append.
                current_addr = st.session_state.wallet_data.get("address")
                if current_addr:
                    if isinstance(current_addr, dict):
                        st.session_state.wallet_data["address"] = [current_addr, new_address_data]
                    elif isinstance(current_addr, list):
                        st.session_state.wallet_data["address"].append(new_address_data)
                else:
                    st.session_state.wallet_data["address"] = new_address_data

                # Let it rain after a successful operation!
                from streamlit_extras.let_it_rain import rain
                rain(
                    emoji="🎈",
                    font_size=54,
                    falling_speed=5,
                    animation_length="infinite",
                )
                
                logger.success("New address created and added: {}", new_address_data)
            except Exception as e:
                st.error(f"❌ Failed to create new address: {e}")
                logger.error("New address creation failed: {}", e, exc_info=True)

if "wallet_data" in st.session_state:
    with st.container():
        st.markdown("## 💸 Execute Gasless Transaction")
        if "wallet_data" in st.session_state:
            wallet_id = st.session_state.wallet_data.get("wallet_id", "⚠️ Not Available")
        else:
            wallet_id = st.text_input("🔹 Enter Wallet ID for Transfer")
        
        to_address = st.text_input("🔹 Enter Recipient Address")
        amount = st.text_input("💰 Enter Amount to Send")
        asset = st.text_input("🔹 Asset (default is USDC)", value="USDC")

        if st.button("🚀 Execute Gasless Transaction", use_container_width=True):
            try:
                tx_response = cdp_client.execute_gasless_transaction(wallet_id, to_address, amount, asset)
                st.success("✅ Transaction executed successfully!")
                st.json(tx_response)
                from streamlit_extras.let_it_rain import rain
                rain(
                    emoji="🎈",
                    font_size=54,
                    falling_speed=5,
                    animation_length="infinite",
                )
                logger.success("Gasless transaction executed successfully! Details: {}", tx_response)
            except Exception as e:
                st.error(f"❌ Failed to execute gasless transaction: {e}")
                logger.error("Gasless transaction failed: {}", e, exc_info=True)
