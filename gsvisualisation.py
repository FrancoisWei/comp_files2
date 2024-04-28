import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from email.message import EmailMessage
import ssl
import smtplib
from email.utils import formataddr
import os

sender = os.getenv("SENDER")
password = os.getenv("PASSWORD")
receiver = os.getenv("RECEIVER")
subject = 'carbon offset purchase notice'

#obtaining data on quantity
supply=[]
demand=[]

Supply_ID = '1bvbcwO1mhAWRSE8VtzqzjjS8UcE7GLo4JFAeHtsDNHM'
SUPPLYSHEET_NAME = 'Vendors'
url = f'https://docs.google.com/spreadsheets/d/{Supply_ID}/gviz/tq?tqx=out:csv&sheet={SUPPLYSHEET_NAME}'
df = pd.read_csv(url)
supply_sum = df['Emission reduction'].astype(float).sum()


Demand_ID = '1nkTlHniZb2Rcp_mr9Z8YQENdrqkjF8BfmuSkfbXmm1Q'
DEMANDSHEET_NAME ='Vendors'
url_d = f'https://docs.google.com/spreadsheets/d/{Demand_ID}/gviz/tq?tqx=out:csv&sheet={DEMANDSHEET_NAME}'
dfd = pd.read_csv(url_d)
demand_sum = dfd['Purchase amount'].astype(float).sum()

Stock = supply_sum - demand_sum

#page title
st.title("Carbon Offsets Purchase Portal")
st.markdown(f"Currently, there are {Stock} units of carbon offsets up for purchase")
if Stock<0:
    st.markdown("Although there is insufficient stock at the moment, we are still accepting requests for purchase. We will get back to you once there are available offsets")
st.markdown("Enter the details of the new purchase below")

#link to google sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing vendors data
existing_data = conn.read(worksheet="Vendors", usecols=list(range(6)), ttl=5)
existing_data = existing_data.dropna(how="all")  

#List of Business Types
Business_types = [
    "Manufacturer",
    "Distributor",
    "Wholesaler",
    "Retailer",
    "Service Provider",
]
PRODUCTS = [
    "Electronics",
    "Apparel",
    "Groceries",
    "Software",
    "Other",
]

#form
with st.form(key="vendor_form", clear_on_submit= True):
    company_name = st.text_input(label="Company Name*")
    business_type = st.selectbox("Business Type*", options=Business_types, index=None)
    products = st.multiselect("Products Offered", options=PRODUCTS)
    buyer_email = st.text_input("Your email*")
    product_quantity = st.text_input("Quantity of carbon credits that you wish to purchase*")
    date = st.date_input(label="Date of request (Today's date)*")

#Mark required fields
    st.markdown("**required*")
    submit_button = st.form_submit_button(label="Submit Vendor Details")


#necessary checks to ensure that all required fields are filled
    if submit_button:
        if not company_name or not business_type or not buyer_email or not product_quantity or not date:
            st.warning("Ensure all mandatory fields are filled.")
            st.stop()
        else:
            vendor_data = pd.DataFrame(
                    [
                        {
                            "CompanyName": company_name,
                            "BusinessType": business_type,
                            "Products": ", ".join(products),
                            "Email": buyer_email,
                            "Purchase amount": product_quantity,
                            "Date": date.strftime("%Y-%m-%d"),
                        }
                    ]
                )
        #Adding the above info to the existing data
        updated_df = pd.concat([existing_data, vendor_data], ignore_index=True)
        conn.update(worksheet="Vendors", data=updated_df)
        st.success("Your request to purchase has been successfully submitted!")
        
        #email
        body = f"""
        {company_name} of {buyer_email} wants to purchase {product_quantity} of carbon credits, view details at https://docs.google.com/spreadsheets/d/1nkTlHniZb2Rcp_mr9Z8YQENdrqkjF8BfmuSkfbXmm1Q/edit#gid=0
        """
        em = EmailMessage()
        em['From'] = formataddr(("Francois G.D.", sender))
        em['To'] = receiver
        em['subject'] = subject
        em.set_content(body)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
        sent = True
        


    



