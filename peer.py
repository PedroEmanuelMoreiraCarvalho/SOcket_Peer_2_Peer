import socket
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
                print("ja era pra ter acabado")
                break
            listen_thread = Thread(target=self.listenPeer,args=(cli,))
            listen_thread.start()
            
            self.threads.append(listen_thread)
            self.peers.append(cli)
            self.addAddresToHashTable(cli)
            print("nova conexão")
        
    def off(self):
        print("saindo...")
        self.emit("saindo...")
        self.running = False
        socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((self.getIp(),PORT))
        self.server.close()
    
    def listenPeer(self,peer):
        print("ouvinte")
        while self.running:
            try:
                data = peer.recv(1024)
                if data:
                    print(f"from conn{peer.getpeername()}:",data.decode())
                    if(data.decode() == "saindo..."):
                        peer.send(b"saindo_123")
                    if(data.decode() == "saindo_123"):
                        break
            except Exception as e:
                print(e)
                break
        print("conexão com",peer.getpeername(),"encerrada")
        peer.close()
    
    def addAddresToHashTable(self,peer):
        key = self.getHashKey(peer.getpeername()[0])
        self.peers_hash_table[key].append(peer)
    
    def getHashKey(self,address):
        return int(address.split('.')[-1]) % self.capacity
    
    def checkExistence(self,address):
        key = self.getHashKey(address)
        for peer in self.peers_hash_table[key]:
            if(peer.getpeername()[0] == address):
                print("encontrado")
                return peer
        print("não encontrado")
    
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
    
    def emit(self,message):
    	for peer in self.peers:
    		peer.send(message.encode())
    
    def connect(self,host,port):
        conn = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        conn.connect((host,port))
        Thread(target=self.listenPeer,args=(conn,)).start()
        self.peers.append(conn)
        
if __name__ == "__main__":
    peer = Peer()
    print(peer.getIp())
    while True:
        option = int(input("digite a opção:\n1-conectar\n2-enviar mensagem\n3-checar endereço\n4-sair\n>"))
        if option == 1:
            ip = input("Digite o ip:")
            port = PORT
            peer.connect(ip,port)
        elif option == 2:
            msg = input("digite a mensagem:")
            peer.emit(msg)
        elif option == 3:
            address = input("digite o endereço:")
            peer.checkExistence(address)
        elif option == 4:
            peer.off()
            exit()
        else:
            print("opção inválida")
