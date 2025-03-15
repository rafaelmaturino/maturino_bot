from pybit.unified_trading import HTTP
import time

# Configuração da API
key = " "    #coloque sua KEY api
secret = " " #colque sua secret api

session = HTTP(
    testnet=False,  # Defina como True para Testnet
    api_key=key,    
    api_secret=secret  
)

# Função para pegar o preço atual do Bitcoin
def get_btc_price():
    try:
        ticker = session.get_tickers(category="linear", symbol="BTCUSDT")
        price = float(ticker['result']['list'][0]['lastPrice'])
        return price
    except Exception as e:
        print(f"⚠️ Erro ao pegar o preço do BTC: {e}")
        return 0.0

# Função para arredondar o preço ao múltiplo de 10.000 abaixo do preço atual
def calcular_nivel(preco_atual):
    return int(preco_atual // 10000) * 10000  # Exemplo: 83190 → 80000

def verificar_ordens_abertas(preco_entrada):
    try:
        # Verifica ordens abertas no mercado
        ordens = session.get_open_orders(symbol="BTCUSDT", category="linear")
        
        # Se houver ordens abertas
        if 'result' in ordens and ordens['result']['list']:
            for ordem in ordens['result']['list']:
                if ordem['side'] == 'Buy' and float(ordem['price']) == preco_entrada:
                    #print(f"Já existe uma ordem de compra em {preco_entrada} USDT.",end="\r")
                    return True  # Ordem já aberta
        return False  # Nenhuma ordem encontrada
    except Exception as e:
        print(f"⚠️ Erro ao verificar ordens abertas: {e}")
        return False



# Criar ordem de compra no nível calculado
def criar_ordem_compra(preco_entrada):
    print(f"🟢 Criando ordem de compra em {preco_entrada} USDT")

    try:
        response = session.place_order(
            category="linear",
            symbol="BTCUSDT",
            side="Buy",
            orderType="Limit",
            price=preco_entrada,
            qty=0.01,  # Ajuste a quantidade conforme necessário
            timeInForce="GTC"
        )
    
        if response.get("retCode") == 0:
            print("✅ Ordem de compra enviada com sucesso!")
            return True  # Ordem criada com sucesso
        else:
            print(f"⚠️ Erro ao criar ordem: {response.get('retMsg')}")
            return False  # Falha ao criar ordem
    except Exception as e:
        print(f"⚠️ Erro ao enviar ordem de compra: {e}")
        return False

# Função para verificar a posição aberta
def verificar_posicao():
    try:
        position = session.get_positions(symbol="BTCUSDT", category="linear")
        
        # Verifica se a chave 'result' existe e se contém uma lista não vazia
        if 'result' in position and position['result']:
            # Verifica se o tamanho da posição é diferente de 0
            if position['result'][0]['size'] != '0':  
                return float(position['result'][0]['size'])  # Retorna o tamanho da posição
            else:
                print("⚠️ Nenhuma Posição aberta.")
                return 0.0  # Caso não haja posição aberta
        else:
            print("⚠️ Não há posição aberta.")
            return 0.0  # Caso não exista 'result' ou esteja vazio
    except Exception as e:
        #print(f"⚠️ Erro ao verificar posição: {e}")
        return 0.0  # Caso haja erro na consulta

# Criar ordens de Take Profit escalonadas
def criar_take_profit(preco_entrada):
    posicao_atual = verificar_posicao()  # Verifica a posição atual

    if posicao_atual <= 0:
        #print("⚠️ Não há posição aberta.")
        return
    
    qtd_parcial = posicao_atual / 10  # Dividir a posição em 10 partes iguais
    for i in range(1, 11):  # Criar Take Profits de 1.000 em 1.000 até 10.000
        preco_tp = preco_entrada + (i * 1000)  # Aumenta 1.000 a cada iteração
        
        print(f"🎯 Criando Take Profit em {preco_tp} USDT para {qtd_parcial} BTC")

        try:
            response = session.place_order(
                category="linear",
                symbol="BTCUSDT",
                side="Sell",
                orderType="Limit",
                price=preco_tp,
                qty=qtd_parcial,  
                timeInForce="GTC",
                reduceOnly=True
            )

            if response.get("retCode") == 0:
                print(f"✅ Take Profit criado em {preco_tp} USDT!")
            else:
                print(f"⚠️ Erro ao criar Take Profit: {response.get('retMsg')}")
        except Exception as e:
            print(f"⚠️ Erro ao criar Take Profit em {preco_tp}: {e}")

# Lista para armazenar os níveis onde já foram feitas ordens
ordens_abertas = set()

# Loop principal
while True:
    preco_atual = get_btc_price()
    print(f"BTCUSDT: {preco_atual}",end="\r")
    if preco_atual == 0.0:
        print("⚠️ Preço do BTC não disponível. Tentando novamente...")
        time.sleep(10)
        continue  # Ignora o resto do loop caso o preço não seja obtido

    proximo_nivel = calcular_nivel(preco_atual)

    # Se ainda não fizemos uma ordem nesse nível, criamos
    if not verificar_ordens_abertas(proximo_nivel):
        if criar_ordem_compra(proximo_nivel):
            criar_take_profit(proximo_nivel)  # Passa a quantidade total da ordem de compra
            ordens_abertas.add(proximo_nivel)  # Registra a ordem criada

    time.sleep(10)  # Aguarda antes de verificar novamente
