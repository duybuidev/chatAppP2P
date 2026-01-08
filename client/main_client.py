import socket
import threading
import json
import os
import base64
import time


class TerminalClient:
    def __init__(self, server_ip='127.0.0.1', server_port=5001):
        self.server_addr = (server_ip, server_port)
        self.username = ""
        self.p2p_port = None
        self.server_conn = None # Giữ kết nối chính tới Server ở đây

        if self.login():
            threading.Thread(target=self.listen_p2p, daemon=True).start()
            self.menu()

    def login(self):
        print("--- LOGIN TO CHAT SYSTEM ---")
        u = input("Username: ")
        p = input("Password: ")
        self.p2p_port = int(input("Enter your P2P Port: "))

        try:
            # Tạo kết nối và giữ nguyên nó, không đóng!
            self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_conn.connect(self.server_addr)

            data = {"type": "LOGIN", "user": u, "pass": p, "p2p_port": self.p2p_port}
            self.server_conn.send(json.dumps(data).encode('utf-8'))

            res = json.loads(self.server_conn.recv(1024).decode('utf-8'))
            if res['status'] == 'OK':
                self.username = u
                print(f"Login successful! Welcome {u}.")
                return True
        except Exception as e:
            print(f"Server error: {e}")
        return False

    def listen_p2p(self):
        """Luồng này luôn chạy ngầm để nhận dữ liệu từ bạn bè"""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('0.0.0.0', self.p2p_port))
        listener.listen(5)
        while True:
            conn, addr = listener.accept()
            data = conn.recv(1024 * 1024 * 5)  # Max 5MB
            msg = json.loads(data.decode('utf-8'))

            if msg['type'] == 'CHAT':
                print(f"\n[Message from {msg['sender']}]: {msg['content']}")
                print("Your choice: ", end="", flush=True)
            elif msg['type'] == 'FILE':
                filename = msg['filename']
                file_data = base64.b64decode(msg['data'])
                if not os.path.exists("downloads"): os.makedirs("downloads")
                with open(f"downloads/{filename}", "wb") as f:
                    f.write(file_data)
                print(f"\n[File from {msg['sender']}]: {filename} saved to /downloads")
                print("Your choice: ", end="", flush=True)
            conn.close()

    def get_online_list(self):
        """Sử dụng kết nối đang mở để lấy danh sách"""
        try:
            self.server_conn.send(json.dumps({"type": "GET_LIST"}).encode('utf-8'))
            users = json.loads(self.server_conn.recv(4096).decode('utf-8'))
            return users
        except:
            print("Lost connection to Central Server.")
            return {}

    def send_chat(self):
        users = self.get_online_list()
        print("\nOnline users:", ", ".join(users.keys()))
        target = input("Target username: ")
        if target in users:
            msg = input("Enter message: ")
            ip, port = users[target]
            self.send_p2p_packet(ip, port, {"type": "CHAT", "sender": self.username, "content": msg})
        else:
            print("User offline.")

    def send_file(self):
        users = self.get_online_list()
        target = input("Target username: ")
        if target in users:
            file_path = input("Enter file path: ")
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode('utf-8')
                ip, port = users[target]
                packet = {
                    "type": "FILE", "sender": self.username,
                    "filename": os.path.basename(file_path), "data": encoded
                }
                self.send_p2p_packet(ip, port, packet)
                print("File sent!")
            else:
                print("File not found.")

    def send_p2p_packet(self, ip, port, packet):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(json.dumps(packet).encode('utf-8'))
            s.close()
        except:
            print("Could not connect to peer.")

    def menu(self):
        while True:
            print("\n--- MENU ---")
            print("1. List Online Users")
            print("2. Send Message (P2P)")
            print("3. Send File (P2P)")
            print("4. Exit")
            choice = input("Your choice: ")

            if choice == '1':
                users = self.get_online_list()
                print("Online:", users)
            elif choice == '2':
                self.send_chat()
            elif choice == '3':
                self.send_file()
            elif choice == '4':
                break


if __name__ == "__main__":
    try:
        ip = input("Nhập IP Central Server (bỏ trống nếu là 127.0.0.1): ")
        if not ip:
            ip = '127.0.0.1'

        # Gọi lớp TerminalClient với IP vừa nhập
        TerminalClient(server_ip=ip, server_port=5001)
    except KeyboardInterrupt:
        print("\nĐang thoát ứng dụng...")