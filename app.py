from flask import Flask, render_template, request, redirect, url_for
import MySQLdb
import getpass

app = Flask(__name__)

# App config
PORT = 11322 

# Database config
DB_HOST = 'localhost'
DB_USER = 'u05'
DB_NAME = 'u05'
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
    cur.execute("INSERT INTO suppliers(_id, name, email) VALUES (%s, %s, %s)", 
                (details['_id'], details['name'], details['email']))
    cur.execute("INSERT INTO supp_numbers(number,_id) VALUES (%s, %s)", (details['number'], details['_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/annual-expenses', methods=['GET'])
def annual_expenses():
    conn = get_db_connection()
    cur = conn.cursor()
    start_year = request.form['start_year']
    end_year = request.form['end_year']
    cur.execute("SELECT SUM(parts.price * order_items.qty) AS TotalPartsCost FROM parts, order_items, orders WHERE orders._id = order_items.order_id AND parts._id = order_items.part_id AND YEAR(orders.when) BETWEEN %s AND %s",[start_year],[end_year])
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', annual_expenses=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)