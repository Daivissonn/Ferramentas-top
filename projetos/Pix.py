#Vamos fazer um sistema de pagamento com pix, cartão de credito e debito, Pix cola e outras formas de pagamento.
#para ficar mais bonito, e que a gente consiga verificar se o pagamento foi realizado com sucesso, vamos criar uma classe de pagamento com pix, cartão de credito e debito, Pix cola e outras formas de pagamento.
#vamos primeiro criar a classe de pagamento com pix, cartão de credito e debito, Pix cola e outras formas de pagamento.
class pagamento:
    def __init__(self, valor, metodo_pagamento, cartao=None, pix=None):
        self.valor = valor
        self.metodo_pagamento = metodo_pagamento
        self.cartao = cartao
        self.pix = pix

class pix:
    def __init__(self, chave_pix, valor):
        self.chave_pix = chave_pix
        self.valor = valor

    def tipos_de_pix(self, numero, cpf, chave_aleatoria, chave_email, chave_telefone):
        self.numero = numero
        self.cpf = cpf
        self.chave_aleatoria = chave_aleatoria
        self.chave_email = chave_email
        self.chave_telefone = chave_telefone

    def realizar_pagamento(self):
        print(f"Simulação: pagamento de R${self.valor} via Pix.")

#com a classe criado, vamos criar a classe de pagamento com cartão de crédito e débito.

class cartao:
    def __init__(self, numero_cartao, validade, cvv, valor, tipo):
        self.numero_cartao = str(numero_cartao)[-4:]
        self.validade = validade
        del cvv
        self.valor = valor
        self.tipo = tipo #tipo pode ser crédito ou débito

    def realizar_pagamento(self):
        numero_mascarado = f"**** **** **** {self.numero_cartao}"
        print(f"Simulação: pagamento de R${self.valor} via cartão {self.tipo} ({numero_mascarado}).")

#agora vamos criar a classe de pagamento com Pix cola.

class pix_cola:
    def __init__(self, chave_pix_cola, valor):
        self.chave_pix_cola = chave_pix_cola
        self.valor = valor

    def realizar_pagamento(self):
        print(f"Simulação: pagamento de R${self.valor} via Pix copia e cola.")
            