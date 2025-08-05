import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from streamlit_option_menu import option_menu
import streamlit as st
from config import get_api_url
import requests
import os
import json
from io import BytesIO
import threading

DEFAULT_API_URL = "https://automatic-orbit-7v9g9gg95j2x45-8000.app.github.dev/:8000"
API_URL = get_api_url(debug=False)


st.set_page_config(page_title="Receipt Insight", layout="wide")



# --- Sidebar navigation ---

with st.sidebar:
    selected = option_menu(
        menu_title="",
        options=["📊 Summary", "📦 All Purchases", "📤 Upload Receipt", "🛠️ Admin"],
        icons=["bar-chart", "cart", "cloud-upload"],
        default_index=0,
        styles={
            "container": {
                "padding": "0px",
                "background-color": "rgba(0, 0, 0, 0)",  # transparent
            },
            "icon": {
                "color": "#cccccc",
                "font-size": "16px"
            },
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "4px 0",
                "padding": "0.6rem 1rem",
                "border-radius": "6px",
                "color": "#dddddd",
                "background-color": "rgba(0, 0, 0, 0)",  # transparent
                "--hover-color": "#262730"
            },
            "nav-link-selected": {
                "background-color": "#3772ff",
                "color": "#ffffff"
            }
        }
    )




# --- Summary Tab ---
# --- Summary Tab ---
if selected == "📊 Summary":
    st.subheader("📊 Summary")

    # --- Rest of summary content loads here ---
    st.markdown("📅 Overview of your spending, top categories, etc.")
    # Add charts, stats, summaries here...
    summary = requests.get(f"{API_URL}/summary").json()["summary"]
    
    # Sub-tabs for summary
    tab1, tab2, tab3, tab4 = st.tabs(["📅 By Date", "🧾 By Receipt", "🛒 By Item", "📈 Trends"])

    with tab1:
        st.subheader("📅 Spend by Date")
        df = pd.DataFrame(summary["by_date"])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            st.bar_chart(df)
            st.dataframe(df)

    with tab2:
        st.subheader("🧾 Spend by Receipt")
        df = pd.DataFrame(summary["by_receipt"])
        st.dataframe(df)

    with tab3:
        st.subheader("🛒 Spend by Item")
        df = pd.DataFrame(summary["by_item"])
        st.dataframe(df)
    
    with tab4:
        st.subheader("📈 Trend Analysis (via Jot)")

        if "summary_alerts" not in st.session_state:
            st.session_state["summary_alerts"] = None
        if "alerts_fetched" not in st.session_state:
            st.session_state["alerts_fetched"] = False
        if "alerts_loading" not in st.session_state:
            st.session_state["alerts_loading"] = False

        # Automatically fetch insights if not fetched yet
        if not st.session_state["alerts_fetched"] and not st.session_state["alerts_loading"]:
            st.session_state["alerts_loading"] = True
            st.rerun()

        # Refresh button to force new API call
        if st.button("🔄 Refresh Insights"):
            st.session_state["alerts_fetched"] = False
            st.session_state["alerts_loading"] = True
            st.session_state["summary_alerts"] = None
            st.rerun()

        # Fetch insights from API if loading
        if st.session_state["alerts_loading"]:
            with st.spinner("⏳ Fetching insights from Jot agent..."):
                try:
                    resp = requests.get(f"{API_URL}/summary-alerts")
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state["summary_alerts"] = data.get("alerts", "⚠️ No alerts returned.")
                        st.session_state["alerts_fetched"] = True
                        st.session_state["alerts_loading"] = False
                        st.rerun()
                    else:
                        st.error(f"❌ API Error: {resp.status_code}")
                        st.session_state["alerts_loading"] = False
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
                    st.session_state["alerts_loading"] = False

        # Show insights if available
        if st.session_state.get("summary_alerts"):
            with st.expander("📣 Jot Agent Insights", expanded=True):
                st.markdown(st.session_state["summary_alerts"])




    

# --- All Purchases Tab ---
elif selected == "📦 All Purchases":
    st.header("📦 All Saved Purchases")

    try:
        response = requests.get(f"{API_URL}/purchases")
        if response.status_code != 200:
            st.error("❌ Failed to fetch purchases from API.")
        else:
            data = response.json().get("data", [])
            if not data:
                st.info("No purchases found yet.")
            else:
                df = pd.DataFrame(data)

                # Group by receipt
                for receipt_title, group in df.groupby("receipt_title"):
                    with st.expander(f"🧾 {receipt_title} — {group['purchase_date'].iloc[0]}"):
                        # Show table of items
                        item_table = group[["item", "quantity", "price"]].copy()
                        item_table["price"] = item_table["price"].apply(lambda x: f"${x:.2f}")
                        st.table(item_table.reset_index(drop=True))

                        # Show image if exists
                        image_file = group["image_filename"].iloc[0]
                        image_path = f"app/data/receipts/{image_file}"

                        try:
                            if os.path.exists(image_path):
                                with open(image_path, "rb") as img_file:
                                    st.image(img_file.read(), caption=image_file, width=250)
                            else:
                                st.caption("📁 Image not found.")
                        except Exception as e:
                            st.warning(f"⚠️ Could not display image: {e}")

                        # Delete button
                        delete_key = f"delete_{receipt_title}"
                        confirm_key = f"confirm_{receipt_title}"

                        if st.button(f"🗑️ Delete Receipt: {receipt_title}", key=delete_key):
                            st.session_state[confirm_key] = True

                        if st.session_state.get(confirm_key):
                            st.warning(f"Are you sure you want to delete '{receipt_title}'?")
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("✅ Yes, Delete", key=f"confirm_yes_{receipt_title}"):
                                    delete_response = requests.delete(f"{API_URL}/receipt/{receipt_title}")
                                    if delete_response.status_code == 200:
                                        st.success("✅ Deleted successfully.")
                                        st.session_state.pop(confirm_key, None)
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete receipt.")
                            with col2:
                                if st.button("❌ Cancel", key=f"confirm_no_{receipt_title}"):
                                    st.session_state.pop(confirm_key, None)


    except Exception as e:
        st.error(f"❌ Error loading purchases: {e}")



# --- Upload Receipt Tab ---
elif selected == "📤 Upload Receipt":


    st.header("📤 Upload a New Receipt")
    uploaded_file = st.file_uploader("Choose or capture a receipt", 
                                     type=["jpg", "jpeg", "png", "heic"]  # ✅ Add HEIC
                                    )


    if uploaded_file:
        receipt_bytes = uploaded_file.getvalue()
        receipt_file_name = uploaded_file.name
        receipt_name_default = os.path.splitext(uploaded_file.name)[0]
        receipt_name = st.text_input("📝 Edit Receipt Name (optional)", value=receipt_name_default)

        # Store the uploaded bytes and name in session (so they persist across reruns)
        st.session_state["uploaded_bytes"] = receipt_bytes
        st.session_state["receipt_name"] = receipt_name

        if st.button("Parse & Preview") or "preview_data" in st.session_state:
            if "preview_data" not in st.session_state:
                with st.spinner("🔍 Parsing receipt with GPT..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/upload-preview",
                            files={"file": (uploaded_file.name, BytesIO(receipt_bytes), uploaded_file.type)},
                            data={"receipt_name": receipt_name},
                        )
                        data = res.json()
                        if data.get("status") == "success":
                            st.session_state["preview_data"] = data
                        else:
                            st.error("❌ Error during preview generation.")
                            st.stop()
                    except Exception as e:
                        st.error(f"❌ API call failed: {e}")
                        st.stop()

            data = st.session_state["preview_data"]
            st.image(BytesIO(st.session_state["uploaded_bytes"]), caption="📷 Receipt Image", use_container_width=True)
            st.subheader("🧾 Select Line Items to Save")

            selected_purchases = []
            for i, p in enumerate(data["purchases"]):
                label = f"{p['item']} — Qty: {p['qty']} — Price: {p['price']}"
                checked = st.checkbox(label, value=True, key=f"item_{i}")
                if checked:
                    selected_purchases.append(p)

            if st.button("💾 Save Selected Items to DB"):
                payload = {
                    "receipt_title": data["receipt_title"],
                    "image_filename": receipt_file_name,  # wherever you store it
                    "date": data["date"],
                    "purchases": selected_purchases
                }


                save_res = requests.post(f"{API_URL}/save", json=payload)
                if save_res.status_code == 200:
                    st.success("✅ Saved successfully!")
                    del st.session_state["preview_data"]
                else:
                    st.error(f"❌ Save failed: {save_res.text}")


elif selected == "🛠️ Admin":
    st.header("🔧 Admin Tools")
    st.warning("⚠️ This will permanently delete all purchase and receipt data.")

    if "confirming_reset" not in st.session_state:
        st.session_state.confirming_reset = False

    # First stage: Show the initial button
    if not st.session_state.confirming_reset:
        if st.button("❌ Drop All Purchases"):
            st.session_state.confirming_reset = True

    # Second stage: Ask for confirmation
    if st.session_state.confirming_reset:
        confirmed = st.checkbox("I understand and want to proceed")

        if st.button("✅ Confirm Delete"):
            if confirmed:
                try:
                    res = requests.post("http://localhost:8000/admin/reset")
                    if res.ok and res.json().get("status") == "success":
                        st.success("✅ All data deleted.")
                        st.session_state.confirming_reset = False
                    else:
                        st.error("❌ Failed to reset data.")
                except Exception as e:
                    st.error(f"🚨 API call failed: {e}")
            else:
                st.warning("Please confirm by checking the box.")
