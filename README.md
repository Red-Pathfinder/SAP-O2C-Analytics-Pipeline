# SAP SD Order-to-Cash (O2C) Analytics

This is my final capstone project for the SAP Data Analytics elective.

Since I didn't have access to a live SAP server or HANA database to pull from, I built a Python script that simulates the whole Order-to-Cash (O2C) data pipeline from scratch. It generates realistic relational data, processes it, and spits out an analytics dashboard to track things like SLA breaches and unbilled revenue.

### How the data works (SAP Tables)

I wanted to make the database architecture as authentic to real SAP as possible. Instead of using flat files, the script simulates these core SD tables and joins them:

| Table | Business Entity | What it tracks |
| :--- | :--- | :--- |
| **VBAK** | Sales Order Header | The main order date and total value |
| **VBAP** | Sales Order Item | Individual materials and quantities |
| **LIKP** | Delivery Header | When goods were actually issued |
| **VBRK** | Billing Header | The invoice date |

### The join logic (Why I didn't just use inner joins)

If you just inner join these tables, you end up losing all your open orders (sales that haven't been delivered or billed yet). In the real world, tracking those open items is the whole point of a supply chain dashboard.

To fix this, the pipeline uses a cascading Left Join strategy:

1.  **Inner Join** VBAK and VBAP (since an order needs items to be valid).
2.  **Left Join** LIKP (keeps undelivered orders in the dataset).
3.  **Left Join** VBRK (keeps delivered but unbilled orders).

### What it actually calculates

The script takes all the raw timestamps and outputs a few main things:

  * **Order-to-Delivery Lead Time:** Subtracts the order date from the goods issue date to get actual business days.
  * **SLA Tracking:** Color-codes the orders based on if they were delivered in under 7 days, 8-14 days, or breached.
  * **AR Risk:** Calculates the exact amount of money tied up in goods that were delivered but not yet billed.

### Built with

  * **Python 3.11**
  * **Pandas & Numpy** (for the data generation and multi-table merges)
  * **Matplotlib** (for building the dashboard and charts)

### How to run it locally

1.  Clone this repo:
    ```bash
    git clone https://github.com/Red-Pathfinder/SAP-O2C-Analytics-Pipeline.git
    ```
2.  Make sure you have the requirements installed:
    ```bash
    pip install pandas numpy matplotlib
    ```
3.  Run the script:
    ```bash
    python sap_o2c_simulation.py
    ```

The script will print out the summary KPIs in your terminal and save the `sap_o2c_dashboard.png` file directly into the folder.

-----

*Pragyan Prayas Jena | KIIT University | B.Tech CSE (2023-2027)*
