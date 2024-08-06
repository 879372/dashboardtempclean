import fdb

hostname = 'localhost'
database = 'C:/TNC/Dados/DADOS.FDB'
user = 'SYSDBA'
password = 'masterkey'
charset = 'ANSI'

try:
    conn = fdb.connect(
        host=hostname, database=database,
        user=user, password=password,
        charset=charset, fb_library_name='C:\Program Files (x86)\Firebird\Firebird_3_0\fbclient.dll'
    )

    cursor = conn.cursor()    
    cursor.execute("SELECT * FROM pessoa")
    
    for row in cursor.fetchall():
        print(row)
    
    cursor.close()
    conn.close()

except fdb.Error as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
