import pandas as pd
import os
import argparse
import re

def extract_final_amount(memo_field):
    # Extract amounts and take the maximum value directly within the aggregation step
    max_value = 0.0
    for memo in memo_field:
        amounts = re.findall(r'Final amount: £([0-9]+(?:\.[0-9]+)?)', memo)
        if amounts:
            current_max = max(float(amt) for amt in amounts)
            max_value = max(max_value, current_max)
    return max_value

def process_invoice(file_path):
    df = pd.read_csv(file_path, skiprows=5)
    df = df[df['Item number'].notna()]
    df['Date'] = pd.to_datetime(df['Date'].str.slice(0, -4))
    
    agg_funcs = {
        'Date': 'first',
        'Description': 'first',
        'Memo': extract_final_amount,
        'Net amount': 'sum',
        'VAT amount': 'sum'
    }
    grouped = df.groupby('Item number').agg(agg_funcs)
    
    grouped.columns = ['Sale Date', 'Description', 'Total Sale Price', 'Total Fees', 'Total VAT Charged']
    grouped['Shipping Cost'] = 4.45 #placeholder
    grouped['Item Cost'] = 0.00 #placeholder
    grouped['Profit'] = grouped['Total Sale Price'] - grouped['Total Fees'] - grouped['Shipping Cost'] - grouped['Item Cost']
    

    monetary_columns = ['Total Sale Price', 'Total Fees', 'Total VAT Charged', 'Shipping Cost', 'Item Cost', 'Profit']
    grouped[monetary_columns] = grouped[monetary_columns].round(2)
    return grouped

def process_all_invoices(directory, start_date, end_date):
    all_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            invoice_data = process_invoice(file_path)
            all_data.append(invoice_data)
    final_df = pd.concat(all_data) if all_data else pd.DataFrame()
    final_df = final_df[(final_df['Sale Date'] >= start_date) & (final_df['Sale Date'] <= end_date)]
    return final_df.sort_values('Sale Date')

def main():
    parser = argparse.ArgumentParser(description="Process eBay invoice CSV files.")
    parser.add_argument("directory", type=str, help="Directory containing CSV files of eBay invoices")
    parser.add_argument("--start_date", type=pd.to_datetime, default='2023-04-06', help="Start date for filtering (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=pd.to_datetime, default='2024-04-05', help="End date for filtering (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    final_data = process_all_invoices(args.directory, args.start_date, args.end_date)
    
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:,.2f}'.format)
    
    final_data.to_csv('ebay_sales.csv', index=False)

if __name__ == "__main__":
    main()
