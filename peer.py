import socket
import os
import time
from threading import Thread

PORT = 50001        

class Peer():
    def __init__(self):
        self.peers = []
        self.server = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        self.running = True
        self.listen(PORT)
        
        self.threads = []
        
        self.waiting_book = False
    
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
            print("nova conexão")
        
    def off(self):
        print("saindo...")
        self.emit("saindo...","turning_off")
        self.running = False
        socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((self.getIp(),PORT))
        self.server.close()
    
    def listenPeer(self,peer):
        print("ouvindo")
        while self.running:
            try:
                data = peer.recv(1024)
                if data:
                    received_message = data.decode().split(":2:",1)
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
        self.peers.remove(peer_to_remove)
    
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
        elif mode == "searching_book":
            info = content[1:-1].split("::",1)
            
            searched_book = info[0]
            visiteds = info[1]
            
            self.checkPathToBook(searched_book,visiteds)
        elif mode == "send_back":
            info = content[1:-1].split("::3::",1)
            
            path = info[0]
            book = info[1]
            
            self.sendBookBack(path,book)
    
    def connect(self,host,port):
        try:
            conn = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
            conn.connect((host,port))
            Thread(target=self.listenPeer,args=(conn,)).start()
            self.peers.append(conn)
        except Exception as e:
            print("Algo deu errado na conexão:",e)
        
    def getBooks(self):
        path = ".//books"
        try:
            books_list = os.listdir(path)
            return books_list
        except Exception as e:
            return []
    
    def createBook(self,title,content):
        try:
            book_file_dir = ".//books//" + title + ".txt"
                
            f = open(book_file_dir, "w")
            f.write(content)
            f.close()
        except Exception as e:
            print("erro na criação de livro:",e)
    
    def sendBookBack(self,path,book):
        final_path = path.split(",")
        final_path.pop()
        if(len(final_path) == 0):
            try:
                content = book.split("::",1)

                titulo = content[0]
                book_text = content[1]
                
                book_file_dir = ".//books//" + titulo
                
                f = open(book_file_dir, "w")
                f.write(book_text)
                f.close()
                
                self.waiting_book = False
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
        
        if self.checkBook(book_searched):
            book_coded = self.encodeBook(book_searched)
            self.sendBookBack(previous_path[0:-1],book_coded)
            return
        
        search_message = self.getPathSearchMessage(book_searched,previous_path)
        self.emit(search_message,"searching_book")
        
    def encodeBook(self,book_name):
        try:
            book_path = ".//books//" + book_name
            book_file = open(book_path, "r")
            book = book_file.read()
            
            book = book_name +"::"+ book
            
            return book 
        except Exception as e:
            print("algo deu errado:",e)
                
    def getPathSearchMessage(self,book_searched,previous_path):
        final_path = ""
        for char in str(previous_path):
            if(char != "'" or char != '"'):
                final_path += char
                
        message = book_searched + "::" + final_path
        return message
        
    def waitBook(self):
        self.waiting_book = True
        count = 0
        
        while self.waiting_book:
            if count % 10 == 0:
                print("   esperando livro...")
            count += 1
            time.sleep(0.1)
            if count == 30:
                print("livro não encontrado")
                return
        
        print("livro encontrado")
        
    def checkBook(self,book_searched):
        books_getted = self.getBooks()
        if book_searched in books_getted:
            return True
        return False
    
    
if __name__ == "__main__":
    if not os.path.exists(".//books"):
        os.makedirs(".//books")
    
    peer = Peer()
    print(peer.getIp())
    
    while True:
        try:
            print("====================================================")
            option = input("digite a opção:\n1-conectar\n2-procurar livro\n3-escrever livro\n4-livros possuídos\n5-sair\n>").strip()
            if option == "1":
                ip = input("Digite o ip:")
                port = PORT
                peer.connect(ip,port)
            elif option == "2":
                book = input("digite o nome do livro:")
                if peer.checkBook(book):
                    print("Livro já obtivo")
                else:
                    peer.checkPathToBook(book,'')
                    peer.waitBook()
            elif option == "3":
                title = input("digite o título:")
                content = input("digite o conteúdo:")
                peer.createBook(title,content)
            elif option == "4":
                books = peer.getBooks()
                print("livros possuídos:")
                if len(books) == 0:
                    print("   nenhum livro possuído")
                for book in books:
                    print("   -",book)
            elif option == "5":
                peer.off()
                exit()
            else:
                print("opção inválida")
        except Exception:
            print("algo deu errado...")