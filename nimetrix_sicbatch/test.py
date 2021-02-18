import pyodbc 
# Some other example server values are
# server = 'localhost\sqlexpress' # for a named instance
# server = 'myserver,port' # to specify an alternate port
server = 'tcp:52.36.41.94' 
database = 'Sicbatch2012' 
username = 'Sicbatch' 
password = 'zaq1XSW@' 
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()
myrows = cursor.execute("SELECT @@VERSION").fetchall()
print(myrows)
cursor.close()
cnxn.close()
