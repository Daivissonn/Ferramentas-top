#include <stdio.h>
#include <sys/socket.h>
#include <netdb.h>

int main(int argc, char *argv[]) {

    int meusoquete;
    int conecta;

    int porta;
    int inicio = 0;
    int final = 65535;
    char *destino;
    destino = argv[1];

    struct sockaddr_in alvo;
    
    for (porta = inicio; porta <= final; porta++) {

    meusoquete = socket(AF_INET, SOCK_STREAM, 0);
    alvo.sin_family = AF_INET;
    alvo.sin_port = htons(porta);
    alvo.sin_addr.s_addr = inet_addr(destino);

    conecta = connect(meusoquete, (struct sockaddr *)&alvo, sizeof(alvo));

    if (conecta == 0) {
        printf("Porta %d -status [ABERTA]\n", porta);
        close(meusoquete);
        close(conecta);
    } else {
        close(meusoquete);
        close(conecta);
    }
}
}