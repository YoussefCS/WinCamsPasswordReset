import pyodbc

class SQLConnector:
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    def connect(self):
        try:
            conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
            conn = pyodbc.connect(conn_str)
            return conn
        except pyodbc.Error as e:
            print(f"Error connecting to SQL Server: {e}")
            return None

    def execute_stored_procedure(self, procedure_name, *args, fetch_type= True):
            
            try:
                conn = self.connect()
                result = False
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(f"EXEC {procedure_name} " + ",".join("?" * len(args)), *args)
                    if fetch_type == True:
                        result = cursor.fetchall()  # Fetch all rows returned by the procedure
                    else:
                        result = True
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return result  # Return the fetched result set
                else:
                    return None  # Return None if connection fails
            except pyodbc.Error as e:
                print(f"Error executing stored procedure: {e}")
                return None  # Retu