# 🛡️ Advanced Hybrid DDoS Simulator (AHD-S)

> **Ferramenta de Stress Testing de Alto Desempenho**
> Um simulador de ataques DDoS multi-protocolo escrito em Python, C#, Java e Assembly. Projetado para testar a resiliência de CDNs (Cloudflare, Vercel), firewalls e servidores de aplicação sob condições de carga extrema.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura de Ataques](#arquitetura-de-ataques)
- [Detalhamento Técnico dos Ataques](#detalhamento-técnico-dos-ataques)
- [Como Usar (CLI)](#como-usar-cli)
- [Exemplos de Uso](#exemplos-de-uso)
- [Análise de Resultados](#análise-de-resultados)
- [Boas Práticas de Teste](#boas-práticas-de-teste)

---

## 📊 Visão Geral

O **AHD-S** não é apenas um script de "inundação" simples. Ele implementa uma estratégia de ataque **Polimórfico Híbrido**, que combina vulnerabilidades de diferentes camadas do modelo OSI simultaneamente. O objetivo é esgotar recursos críticos do alvo: **Banda Larga**, **Pool de Conexões**, **CPU (Parsing)** e **Memória**.

| Camada OSI | Tipo de Ataque | Recurso Esgotado |
| :--- | :--- | :--- |
| **L7 (Aplicação)** | HTTP/2 Rapid Reset, Slowloris | Workers, Threads, CPU |
| **L4 (Transporte)** | TCP SYN Flood, UDP Flood | Backlog de Conexões, Buffer de Ponto |
| **L3 (Rede)** | DNS Amplification, TCP Exotic Flags | Banda de Saída, CPU do Kernel |
| **L7 (Protocolo)** | Header Smuggling (CL/TE) | Consistência do Proxy, Cache |

---

## ⚔️ Detalhamento Técnico dos Ataques

### 1. 💨 UDP Flood
- **Mecanismo**: Envia datagramas UDP em alta taxa (10k+ pps) com payloads de 512 bytes.
- **Impacto**: UDP é "fire-and-forget". O servidor de destino deve processar o pacote e tentar responder a um IP que pode não existir (spoofed). Isso força o kernel a consumir CPU para descartar pacotes e o roteador a consumir banda.
- **Uso**: Ideal para testar a capacidade de rate-limiting de L4.

### 2. 🌐 TCP SYN Flood (Connect Flood)
- **Mecanismo**: Inicia milhares de handshakes TCP simultâneos. No modo `hybrid`, usa `AsynchronousSocketChannel` (Java) ou `ThreadPoolExecutor` (Python/C#) para manter o backlog de conexões (`listen backlog`) cheio.
- **Impacto**: O servidor reserva memória para cada conexão "meio-aberta". Quando o backlog atinge o limite (`net.core.somaxconn`), novos clientes legítimos começam a ser rejeitados.
- **Uso**: Testa a configuração de `syncookies` e a tolerância do load balancer.

### 3. 🐌 Slowloris (Resource Exhaustion)
- **Mecanismo**: Abre conexões HTTP e envia headers lentamente (ex: 1 header a cada 500ms).
- **Impacto**: Mantém o worker do servidor web (Nginx, Apache, Node.js) ocupado. Como o servidor não sabe que a requisição está "parada", ele não fecha a conexão. Em poucos minutos, todos os workers ficam presos em requisições de baixo valor.
- **Uso**: Testa os timeouts de `keep-alive` e a limitação de conexões por IP.

### 4. ⚡ HTTP/2 Rapid Reset
- **Mecanismo**: Abre múltiplos *streams* HTTP/2 e envia `RST_STREAM` imediatamente após o envio dos headers.
- **Impacto**: O protocolo HTTP/2 permite milhares de streams em uma única conexão TLS. Abrir e resetar streams rapidamente força o proxy (Cloudflare/Vercel) a alocar e liberar recursos de estado constantemente, causando *CPU Spikes* e potencialmente fazendo o servidor rejeitar novas conexões.
- **Uso**: Testa a proteção contra *Stream Exhaustion* em proxies modernos.

### 5. 📦 Header Smuggling (CL/TE Mismatch)
- **Mecanismo**: Envia requisições com cabeçalhos `Content-Length` e `Transfer-Encoding` conflitantes ou malformados.
- **Impacto**: Explora diferenças de parsing entre o proxy de borda (Cloudflare) e o servidor de origem (Origin). Isso pode permitir que pacotes "fantasma" fiquem presos no buffer, corrompendo requisições de usuários legítimos ou permitindo a injeção de payloads.
- **Uso**: Valida a consistência do WAF e a proteção contra *Request Smuggling*.

### 6. 🔍 DNS Amplification
- **Mecanismo**: Envia requisições DNS pequenas para refletidores públicos (1.1.1.1, 8.8.8.8) com o IP de origem spoofed para o alvo.
- **Impacto**: Registros `AAAA` ou `ANY` podem retornar respostas muito maiores que a pergunta. Se o alvo for um CDN, ele receberá uma quantidade massiva de tráfego de resposta que ele não pediu, esgotando sua banda de saída.
- **Uso**: Testa a proteção contra *Reflection Attacks* e a qualidade do filtro de DNS upstream.

### 7. 🎲 TCP Exotic Flags (NULL/Xmas/Fin)
- **Mecanismo**: Envia pacotes TCP com combinações de flags inválidas (ex: SYN+FIN, ou nenhuma flag).
- **Impacto**: Força o stack de rede do SO (Linux/Windows) a processar estados de conexão ineficientes. Alguns firewalls de software podem consumir CPU excessiva tentando classificar pacotes "ilegais".
- **Uso**: Testa a robustez do *Packet Filter* e a resposta a tráfego de baixo nível.

---

## 💻 Como Usar (CLI)

O script aceita argumentos posicionais e nomeados.

### Sintaxe Básica

```bash
python attack_ddos.py <target> [opções]
```

### Opções Disponíveis

| Flag | Descrição | Padrão |
| :--- | :--- | :--- |
| `target` | IP ou Domínio de destino | Obrigatório |
| `-t, --type` | Tipo de ataque: `hybrid`, `udp`, `tcp`, `http`, `slowloris`, `dns`, `smuggling` | `hybrid` |
| `-d, --duration` | Duração do ataque em segundos | `60` |
| `-p, --port` | Porta de destino | `80` |
| `-i, --intensity` | Taxa alvo de pacotes por segundo (indicativo) | `1000` |

### Exemplos de Uso

#### 1. Ataque Híbrido Total (Cloudflare Breaker)
```bash
python attack_ddos.py cloudflare.com -t hybrid -d 300
```
*Executa todos os vetores simultaneamente contra o domínio `cloudflare.com` por 5 minutos.*

#### 2. Teste de Resiliência HTTP/2
```bash
python attack_ddos.py api.vercel.app -t http2 -p 443 -d 60
```
*Foca exclusivamente no Rapid Reset de streams HTTP/2 na porta TLS.*

#### 3. Esgotamento de Workers (Slowloris)
```bash
python attack_ddos.py myapp.com -t slowloris -d 120
```
*Mantém 100 conexões abertas por 2 minutos para testar o limite de threads.*

#### 4. Ataque de Banda (DNS + UDP)
```bash
python attack_ddos.py 1.1.1.1 -t dns -d 30
```
*Foca na amplificação de DNS para testar a banda de saída.*

#### 5. Validação de WAF (Header Smuggling)
```bash
python attack_ddos.py target.com -t smuggling -d 60
```
*Envia pacotes CL/TE mismatch para testar a proteção do proxy.*

---

## 📈 Análise de Resultados

O script exibe um resumo em tempo real:

```text
[12:00:01] 🎯 Alvo: cloudflare.com (104.16.132.229)
[12:00:01] 📊 Tipo: HYBRID | Duração: 60s | Porta: 80
[12:00:01] ✅ Thread UDP-Flood iniciada.
[12:00:01] ✅ Thread TCP-SYN-Flood iniciada.
[12:00:02] 📊 Pacotes enviados: 1024 | PPS atual: 1024.00
[12:00:03] 📊 Pacotes enviados: 2150 | PPS atual: 1075.00
...
==================================================
📈 RESUMO DO ATAQUE
⏱️  Duração total: 60.02s
📦 Pacotes totais: 65432
📊 PPS médio: 1090.18
==================================================
```

### Métricas de Sucesso (O que observar no Alvo)
1. **Latência (TTFB)**: Aumento no *Time To First Byte* para usuários legítimos.
2. **Taxa de Erros (5xx)**: Aparecimento de `502 Bad Gateway` ou `503 Service Unavailable`.
3. **Throughput**: Queda no número de requisições bem-sucedidas por segundo.
4. **CPU do Alvo**: Pico em threads de parsing HTTP ou kernel network.

---

## 🛠️ Boas Práticas de Teste

1. **Ambiente Isolado**: Nunca execute este script em produção sem autorização. O tráfego pode afetar usuários reais.
2. **Privilégios de Root**: Para o `TCP SYN Flood` com spoofing de IP (raw sockets), execute com `sudo`. Sem root, o script usará o IP local como origem.
3. **Monitoramento**: Use ferramentas como `nload`, `iftop` ou `Wireshark` para capturar o tráfego gerado e validar a eficácia dos vetores.
4. **Escalonamento**: Para simular um ataque real de Tbps, combine múltiplas instâncias deste script em diferentes máquinas (botnet simulada) usando um orquestrador central.
5. **Ajuste de Intensidade**: O parâmetro `-i` é um alvo. A intensidade real depende da sua banda de saída. Para maximizar, use máquinas com conexões simétricas de alta velocidade.

---

## 📂 Estrutura do Projeto

```
attack_ddos/
├── attack_ddos.py      # Implementação principal em Python
├── AdvancedDDOSAttacker.cs # Implementação em C# (.NET 6+)
├── AdvancedDDOSAttacker.java # Implementação em Java (JDK 11+)
├── attack_ddos.asm     # Implementação em Assembly x86-64 (NASM)
├── README.md           # Este arquivo
└── requirements.txt    # Dependências Python (dnspython, h2)
```

### Dependências Python

```bash
pip install dnspython h2
```