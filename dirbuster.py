import requests

response = requests.get('https://example.com')
print(response)

#Montei um script simples para testar a resposta de uma URL usando a biblioteca requests do Python. O código faz uma requisição GET para 'https://example.com' e imprime o objeto de resposta. example: se tem algo na pagina, ele me retorna o status code 200, caso contrário, ele retorna um erro como 404 ou 500.

#o requests é uma biblioteca popular em Python para fazer requisições HTTP de forma simples e eficiente. Ela permite enviar solicitações GET, POST, PUT, DELETE, entre outras, e lidar com respostas de maneira fácil.