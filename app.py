import streamlit as st
import pandas as pd
import qrcode
import os
from datetime import datetime
import geocoder

# ----------- SETTINGS -----------
st.set_page_config(page_title="Makkah Autos", layout="centered")

PRODUCT_FILE = "products.csv"
SCAN_FILE = "scans.csv"
COUNTER_FILE = "counter.txt"
STICKER_FOLDER = "stickers"

# ----------- CREATE FILES -----------
if not os.path.exists(STICKER_FOLDER):
    os.makedirs(STICKER_FOLDER)

if not os.path.exists(PRODUCT_FILE):
    pd.DataFrame(columns=["code"]).to_csv(PRODUCT_FILE, index=False)

if not os.path.exists(SCAN_FILE):
    pd.DataFrame(columns=["code","name","phone","location","time"]).to_csv(SCAN_FILE, index=False)

if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        f.write("0")

# ----------- LOAD DATA -----------
products = pd.read_csv(PRODUCT_FILE)
scans = pd.read_csv(SCAN_FILE)

# ----------- FUNCTION (UNIQUE CODE) -----------
def get_next_codes(n):
    with open(COUNTER_FILE, "r") as f:
        last = int(f.read().strip())

    codes = []
    for i in range(1, n+1):
        code = f"MA{str(last+i).zfill(5)}"
        codes.append(code)

    with open(COUNTER_FILE, "w") as f:
        f.write(str(last + n))

    return codes

# ----------- SESSION -----------
if "admin" not in st.session_state:
    st.session_state.admin = False

# ----------- QR SCAN DETECT -----------
query_code = st.query_params.get("code", None)

# ----------- CUSTOMER VIEW -----------
if query_code and not st.session_state.admin:
    st.title("Product Verification")

    name = st.text_input("اپنا نام لکھیں")
    phone = st.text_input("اپنا واٹس ایپ نمبر لکھیں")

    if st.button("Submit"):
        if query_code in products["code"].values:
            status = "✅ یہ Original Product ہے"
        else:
            status = "❌ یہ Fake Product ہے"

        g = geocoder.ip('me')
        location = g.city

        new_data = pd.DataFrame([{
            "code": query_code,
            "name": name,
            "phone": phone,
            "location": location,
            "time": datetime.now()
        }])

        new_data.to_csv(SCAN_FILE, mode='a', header=False, index=False)

        st.success(status)

    st.stop()

# ----------- ADMIN LOGIN -----------
if not st.session_state.admin:
    st.title("Admin Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.session_state.admin = True
            st.rerun()
        else:
            st.error("غلط username یا password")

    st.stop()

# ----------- ADMIN PANEL -----------
st.sidebar.title("Admin Panel")
menu = st.sidebar.radio("Menu", ["QR Generate", "Dashboard", "Logout"])

# ----------- LOGOUT -----------
if menu == "Logout":
    st.session_state.admin = False
    st.rerun()

# ----------- QR GENERATE -----------
elif menu == "QR Generate":
    st.header("QR Codes Generate کریں")

    qty = st.number_input("کتنے QR بنانے ہیں؟", min_value=1)

    if st.button("Generate"):
        codes = get_next_codes(qty)

        df_new = pd.DataFrame({"code": codes})
        df_new.to_csv(PRODUCT_FILE, mode='a', header=False, index=False)

        base_url = "http://localhost:8501/?code="

        st.success(f"{qty} QR Codes بن گئے!")

        for code in codes:
            qr = qrcode.make(base_url + code)
            path = f"{STICKER_FOLDER}/{code}.png"
            qr.save(path)

            st.image(path, caption=code)

# ----------- DASHBOARD -----------
elif menu == "Dashboard":
    st.header("Dashboard")

    scans = pd.read_csv(SCAN_FILE)

    st.subheader("تمام Scans")
    st.dataframe(scans)

    st.subheader("Code Count")
    st.bar_chart(scans["code"].value_counts())