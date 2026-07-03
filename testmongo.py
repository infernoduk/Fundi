from pymongo import MongoClient

uri = "mongodb+srv://checkmatetuko_db_user:dero1234@cluster0.lzefubj.mongodb.net/fundi?appName=Cluster0&tlsAllowInvalidCertificates=true"

client = MongoClient(uri)
print(client.server_info())   # Should print server details