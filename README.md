SAP SD Order-to-Cash (O2C) Analytics
This is my final capstone project for the SAP Data Analytics elective.

Since I didn't have access to a live SAP server or HANA database to pull from, I built a Python script that simulates the whole Order-to-Cash (O2C) data pipeline from scratch. It generates realistic relational data, processes it, and spits out an analytics dashboard to track things like SLA breaches and unbilled revenue.

[Upload https://www.google.com/search?q=sap_o2c_dashboard.png here, then replace this line with: ]

How the data works (SAP Tables)
I wanted to make the database architecture as authentic to real SAP as possible. Instead of using flat files, the script simulates these core SD tables and joins them:

VBAK - Sales Order Header (tracks the main order date and total value)

VBAP - Sales Order Item (tracks individual materials and quantities)

LIKP - Delivery Header (tracks when goods were actually issued)

VBRK - Billing Header (tracks the invoice date)

The join logic (Why I didn't just use inner joins)
If you just inner join these tables, you end up losing all your open orders (sales that haven't been delivered or billed yet). In the real world, tracking those open items is the whole point of a supply chain dashboard.

To fix this, the pipeline uses a cascading Left Join strategy. It starts with an inner join for VBAK and VBAP (since an order needs items to be valid), but then left joins LIKP and VBRK. This keeps the undelivered orders in the dataset so we can actually calculate the unbilled AR risk.

What it actually calculates
The script takes all the raw timestamps and outputs a few main things:

Order-to-Delivery Lead Time: Subtracts the order date from the goods issue date to get actual business days.

SLA Tracking: Color-codes the orders based on if they were delivered in under 7 days, 8-14 days, or breached.

AR Risk: Calculates the exact amount of money tied up in goods that were delivered but not yet billed.

Built with
Python 3.11

Pandas & Numpy (for the data generation and multi-table merges)

Matplotlib (for building the dashboard and charts)

How to run it locally
Clone this repo.

Make sure you have the requirements installed:
pip install pandas numpy matplotlib

Run the script:
python sap_o2c_simulation.py
