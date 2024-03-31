from flask import Flask, render_template, request, redirect, url_for
import MySQLdb
import getpass
import re

app = Flask(__name__)

# App config
PORT = 10000 # change this to your port number 

# Database config
DB_HOST = 'localhost'
DB_USER = 'uXX'
DB_NAME = 'uXX'
DB_PASSWORD = getpass.getpass('Enter your MySQL password: ')

def get_db_connection():
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# Display all the data in the entered table name
tables_list = ['parts', 'orders', 'order_items', 'suppliers', 'supp_numbers']
@app.route('/tables', methods=['GET', 'POST'])
def display_table():
    conn = get_db_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        table_name = request.form['myTable']
        if table_name in tables_list:
            cur.execute("SELECT * FROM {}".format(table_name))
            data = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('index.html', table_data=data, table_name=table_name)
        else:
            return "Table not found"
    else:
        return render_template('index.html', tables_list=tables_list)

@app.route('/add-supplier', methods=['POST'])
def add_supplier():
    conn = get_db_connection()
    cur = conn.cursor()
    details = request.form
    phone_numbers = details['phone_numbers'].split(',')
    try:
        # insert supplier into the suppliers table
        cur.execute("INSERT INTO suppliers(_id, name, email) VALUES (%s, %s, %s)", 
                    (details['_id'], details['name'], details['email']))
        # insert any phone numbers associated with a supplier into the supp_number table
        for number in phone_numbers:
            cur.execute("INSERT INTO supp_numbers(number,supp_id) VALUES (%s, %s)", (number.strip(), details['_id']))
        conn.commit()
        return redirect('/')
    except Exception as e:
        if e.args[0] == 1062: # duplicate phone number entry
            table_name = str(e).split(' ')[-1].split('.')[0] # extracting the table name from the error
            dup_value = str(e).split("'")[1] # extracting the duplicate value from the error  
            return f"Error: Duplicate entry in {table_name} table. please change the duplicate value: '{dup_value}'."
        else:
            conn.rollback()
            return "Error: " + str(e)
    finally:
        cur.close()
        conn.close()

@app.route('/annual-expenses', methods=['GET', 'POST'])
def annual_expenses():
    conn = get_db_connection()
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        start_year = request.form['start_year']
        if len(start_year) != 4:
            return "Error: Please enter a valid start year."
        if not eval(start_year) in range(2015,2024):
            return "Error: Start year is out of range."
        end_year = request.form['end_year']
        if len(end_year) != 4:
            return "Error: Please enter a valid end year."
        if not eval(end_year) in range(2015,2024):
            return "Error: End year year is out of range."
        if start_year > end_year:
            return "Error: start year must be before or equal to end year."
        if end_year < start_year:
            return "Error: end year must be after or equal to start year"
        cur.execute("CREATE TEMPORARY TABLE temp_expenses (year INT, total_parts_cost DECIMAL(12, 2))")
        for year in range(int(start_year), int(end_year) + 1):
            cur.execute("""
                        INSERT INTO temp_expenses 
                        SELECT YEAR(orders.when) AS year, 
                          SUM(parts.price * order_items.qty) AS total_parts_cost   
                        FROM parts, order_items, orders 
                        WHERE orders._id = order_items.order_id 
                        AND parts._id = order_items.part_id 
                        AND YEAR(orders.when) = %s
                        GROUP BY year;
                        """, (year,))  
    else:
        return render_template('index.html', show_expenses=False)
    cur.execute("SELECT * FROM temp_expenses")
    data = cur.fetchall()
    cur.execute("DROP TEMPORARY TABLE temp_expenses")
    cur.close()
    conn.close()
    return render_template('index.html', expenses=data, start_year=start_year, end_year=end_year, show_expenses=True)

# Projection
@app.route('/projection', methods=['GET','POST'])
def projection():
  conn = get_db_connection()
  cur = conn.cursor(MySQLdb.cursors.DictCursor)
  if request.method == 'POST':
    percentage = request.form['percentage']
    percentage = percentage.replace("%","")
    percentage = str(float(percentage) / 100.0)

    years = request.form['years']

    cur.execute("CREATE TEMPORARY TABLE temp_budgets (year INT, budget_projection DECIMAL(12,2))")
    for year in range(1, int(years)+1):
      cur.execute("""
                  INSERT INTO temp_budgets 
                  SELECT (YEAR(orders.when)+%s) AS year, 
                    ROUND(SUM(parts.price * order_items.qty) * POW(1 + %s, %s), 2) 
                      AS budget_projection 
                  FROM parts, order_items, orders 
                  WHERE orders._id = order_items.order_id 
                  AND parts._id = order_items.part_id 
                  AND YEAR(orders.when) = 2022 
                  GROUP BY year;
                  """, (str(year), percentage, str(year)))
  else:
    return render_template('index.html', show_budget=False)
  cur.execute("SELECT * FROM temp_budgets")
  data = cur.fetchall()
  cur.execute("DROP TEMPORARY TABLE temp_budgets")
  cur.close()
  conn.close()
  return render_template('index.html', budget_projection = data, years = years, percentage = request.form['percentage'], show_budget=True)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)