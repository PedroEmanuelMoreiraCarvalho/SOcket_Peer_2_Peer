import socket
import os
from threading import Thread

PORT = 50001        

class Peer():
    def __init__(self):
        self.capacity = 7
        self.peers_hash_table = []
        
        for i in range(self.capacity):
            self.peers_hash_table.append([])
        
        self.peers = []
        self.server = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        self.running = True
        self.listen(PORT)
        
        self.threads = []
    
    def listen(self,port):
        ip = self.getIp()
        self.server.bind((ip,port))
        self.server.listen(PORT)
        Thread(target=self.acceptPeers).start()
    
    def acceptPeers(self):
        while self.running:
            cli, addr = self.server.accept()
            
            if self.running == False:
                break
            
            listen_thread = Thread(target=self.listenPeer,args=(cli,))
            listen_thread.start()
            
            self.threads.append(listen_thread)
            self.peers.append(cli)
            self.addAddressToHashTable(cli)
            print("nova conexão")
        
    def off(self):
        print("saindo...")
        self.emit("saindo...","turning_off")
        self.running = False
        socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((self.getIp(),PORT))
        self.server.close()
    
    def listenPeer(self,peer):
        print("ouvinte")
        while self.running:
            try:
                data = peer.recv(1024)
                if data:
                    # print(f"from conn{peer.getpeername()}:",data.decode())
                    
                    received_message = data.decode().split(":2:")
                    self.analyzeMessage(received_message)
                    
                    if(received_message[0] == "turning_off"):
                        peer.send(b"ending:2:saindo_123")
                        break
                    if(received_message[1] == "saindo_123"):
                        print("peer desconectado")
                        break   
            except Exception as e:
                print(e)
                break
        print("conexão com",peer.getpeername(),"encerrada")
        self.removePeer(peer)
        peer.close()
        
    def removePeer(self, peer_to_remove):
        key = self.getHashKey(peer_to_remove.getpeername()[0])
        self.peers.remove(peer_to_remove)
        self.peers_hash_table[key].remove(peer_to_remove)
    
    def addAddressToHashTable(self,peer):
        key = self.getHashKey(peer.getpeername()[0])
        self.peers_hash_table[key].append(peer)
    
    def getHashKey(self,address):
        return int(address.split('.')[-1]) % self.capacity
    
    def getIp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    def checkExistence(self,address, visiteds):
        visiteds.append(self.getIp())
        
        key = self.getHashKey(address)
        
        # checando se endereço está na lista de conexões
        for peer in self.peers_hash_table[key]:
            if(peer.getpeername()[0] == address):
                print("encontrado")
                return peer
            
        for peer in self.peers:
            #verifica se par já foi visitado
            if peer.getpeername()[0] in visiteds:
                continue
            
            visiteds_str = ""
            
            for visited in visiteds:
                visiteds_str += visited + ","
            
            # print("visitados:",visiteds_str)
            content = address + "::" + visiteds_str
            
            message_send = {
                "type": "search",
                "content": content
            }
            
            searching_str = self.encodeString(message_send)
            peer.send(searching_str.encode())
            
        print("não encontrado")
        
    
    def emit(self,message, mode):
        message_send = {
            "type": mode,
            "content": message
        }
        
        encoded_message = self.encodeString(message_send)
        
        for peer in self.peers:
            peer.send(encoded_message.encode())
      
    def emitTo(self, message, mode, address):
        message_send = {
            "type": mode,
            "content": message
        }
        
        encoded_message = self.encodeString(message_send)
        
        for peer in self.peers:
            if peer.getpeername()[0] == address:
                peer.send(encoded_message.encode())
      
    def encodeString(self, message):
        final_message = ""
        final_message += message["type"] + ":2:{" + message["content"] + "}"
        return final_message
        
    def analyzeMessage(self, received_message):
        mode = received_message[0]
        content = received_message[1]
        
        if mode == "send":
            print(content[1:-1]) 
        elif mode == "search":
            info = content[1:-1].split("::") 
            
            address = info[0]
            visiteds = info[1].split(",")

            self.checkExistence(address,visiteds)
        elif mode == "searching_book":
            info = content[1:-1].split("::")
            
            searched_book = info[0]
            visiteds = info[1]
            
            self.checkPathToBook(searched_book,visiteds)
        elif mode == "send_back":
            info = content[1:-1].split("::3::")
            
            path = info[0]
            book = info[1]
            
            self.sendBookBack(path,book)
    
    def connect(self,host,port):
        conn = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        conn.connect((host,port))
        Thread(target=self.listenPeer,args=(conn,)).start()
        self.peers.append(conn)
        self.addAddressToHashTable(conn)
        
    def getBooks(self):
        path = ".//books"
        try:
            books_list = os.listdir(path)
            return books_list
        except Exception as e:
            return []
    
    def sendBookBack(self,path,book):
        final_path = path.split(",")
        final_path.pop()
        if(len(final_path) == 0):
            try:
                f = open(".//books//livro_final.txt", "w")
                f.write(book)
                f.close()
                
                print("livro salvo")
            except Exception:
                print("algo deu errado")
            return
        
        new_path = ""
        for path in final_path:
            new_path += path + ','
            
        message = new_path[0:-1] + "::3::" + book
            
        self.emitTo(mode = "send_back", message = message, address = final_path[-1])
        
    
    def checkPathToBook(self,book_searched,previous_path):
        my_ip = self.getIp()
        
        if my_ip in previous_path:
            return
        
        previous_path += str(my_ip) + ','
        
        books_getted = self.getBooks()
        if book_searched in books_getted:
            book_coded = self.encodeBook(book_searched)
            self.sendBookBack(previous_path[0:-1],book_coded)
            return
        
        search_message = self.getPathSearchMessage(book_searched,previous_path)
        self.emit(search_message,"searching_book")
        
    def encodeBook(self,book_name):
        try:
            book_path = ".//books//" + book_name
            book_file = open(book_path, "r")
        
            return book_file.read()
        except Exception as e:
            print("algo deu errado:",e)
                
    def getPathSearchMessage(self,book_searched,previous_path):
        final_path = ""
        for char in str(previous_path):
            if(char != "'" or char != '"'):
                final_path += char
                
        message = book_searched + "::" + final_path
        return message
        
if __name__ == "__main__":
    if not os.path.exists(".//books"):
        os.makedirs(".//books")
    
    peer = Peer()
    print(peer.getIp())
    
    while True:
        option = input("digite a opção:\n1-conectar\n2-procurar livro\n3-checar endereço\n4-livros possuídos\n5-sair\n>")
        if option == "1":
            ip = input("Digite o ip:")
            port = PORT
            peer.connect(ip,port)
        elif option == "2":
            book = input("digite o nome do livro:")
            peer.checkPathToBook(book,'')
        elif option == "3":
            address = input("digite o endereço:")
            peer.checkExistence(address,[])
        elif option == "4":
            books = peer.getBooks()
            print("livros possuídos:")
            for book in books:
                print("   -",book)
        elif option == "5":
            peer.off()
            exit()
        else:
            print("opção inválida")