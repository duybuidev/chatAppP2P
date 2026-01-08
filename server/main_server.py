import socket
import threading
import json


class CentralServer:
    def __init__(self, host='0.0.0.0', port=5001):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(10)
        self.online_users = {}  # {username: (ip, p2p_port)}
        self.accounts = {"alice": "123", "bob": "123", "admin": "123"}
        print(f"--- CENTRAL SERVER STARTED ON {port} ---")

    def handle_client(self, conn, addr):
        user_auth = None
        while True:
            try:
                raw_data = conn.recv(1024).decode('utf-8')
                if not raw_data:
                    break  # Kết nối bị đóng thực sự

                req = json.loads(raw_data)

                if req['type'] == 'LOGIN':
                    u, p, port = req['user'], req['pass'], req['p2p_port']
                    if self.accounts.get(u) == p:
                        user_auth = u
                        self.online_users[u] = (addr[0], port)
                        conn.send(json.dumps({"status": "OK"}).encode('utf-8'))
                        print(f"[+] {u} logged in and STAYING ONLINE.")
                    else:
                        conn.send(json.dumps({"status": "FAIL"}).encode('utf-8'))

                elif req['type'] == 'GET_LIST':
                    # Gửi danh sách hiện tại cho Client
                    conn.send(json.dumps(self.online_users).encode('utf-8'))

            except Exception as e:
                print(f"Error handling client {user_auth}: {e}")
                break

        # Chỉ khi nào thoát vòng lặp (Client tắt app) mới xóa khỏi danh sách online
        if user_auth:
            if user_auth in self.online_users:
                del self.online_users[user_auth]
            print(f"[-] {user_auth} is now OFFLINE")
        conn.close()

    def run(self):
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    CentralServer().run()