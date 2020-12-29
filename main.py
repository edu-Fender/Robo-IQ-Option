from iqoptionapi.stable_api import IQ_Option
import logging
import userdata
import time
import datetime
import re
import threading
import websocket
import os
import sys
                             #Preço a ser investido
#desabilita uma funcao do debug q atrapalha a visualizacao as vzs
logging.disable(level=(logging.DEBUG))
'''
user = userdata.mainUser
account = IQ_Option(user['username'], user['password'])  # Entra com login e senha da corretora
check, reason = account.connect()
'''
login = "" #colocar o login de alguem aqui e ele passara a ser fixo, nao permitindo que coloquem outra conta
while True:
    senha = input('Senha: ')
    account = IQ_Option(login, senha)  # Entra com login e senha da corretora
    check, reason = account.connect()
    if(check == True):
        time.sleep(1)
        os.system('cls')
        print('Conectado a conta !')
        break
    else:
        print('Não conectado, tente novamente!')
        time.sleep(1)
        os.system('cls')


modo = input('Tipo de conta (REAL OU PRACTICE): ')
account.change_balance(modo)

count = 1                             #Contador
value = int(input('Valor para negocição: '))
lag = int(input('Delay: '))
otc = input("Operar OTC s/n: ")
print('\n\t\t\t\t\t REGEX-BOT\n')
while True:
    if(account.check_connect()==False):
        print('Nao conectado, tentando de novo...!')
    else:
        print('Conectado, executando a lista!')
        break


data = open("sinais.txt").read()        #Abre Sinais.txt
data = re.sub(r" ", "", data)           #Apaga os espaços da lista de sinais, caso exista algum
data = re.sub(r"(^[\S\s]+$)", r"\1\n\nM1\nXXXX\n\nM5\nXXXX\n\nM15\nXXXX\n\nM30\nXXXX\n\n", data) #Adiciona itens ao fim da string para evitar exceções

sinal = re.findall(r"(\d{2}?/\d{2}?/\d{4}?.+)", data)       #Cria array com todos os sinais
expiration = []                                             #Cria array com a expiração de cada sinal
date = re.findall(r"\D(\d{2}?/\d{2}?/\d{4}?)\D", data)      #Cria array com a data (XX/XX/XXXX) de cada sinal
hour = re.findall(r"\D(\d\d:\d\d)\D", data)                 #Cria array com a hora(XX:XX) de cada sinal
active = re.findall(r"\W([A-Z]{6}?)\W", data)              #Cria array com o nome da moeda
action = re.findall(r"\W(CALL|PUT)\W", data)                #Cria array com os actions(ordem) de cada sinal

m1 = re.search(r"(M1\D[\S\s]+?\n\n)", data)      #Separa sinais M1 (expiration 1)
m5 = re.search(r"(M5\D[\S\s]+?\n\n)", data)      #Separa sinais M5 (expiration 5)
m15 = re.search(r"(M15\D[\S\s]+?\n\n)", data)    #Separa sinais M15 (expiration 15)
m30 = re.search(r"(M30\D[\S\s]+?\n\n)", data)    #Separa sinais M30 (expiration 30)

hoje = datetime.date.today()
dia = hoje.day
diasem = hoje.weekday()

#if(account.get_server_timestamp() >= 1596931200):
    #print('expirado')
    #os._exit(1)


#Valor da banca

def append(group, duration):
    for i in range(len(sinal)):
        if (sinal[i] in group): #Separa os sinais de M1 (expiration 1)
            expiration.append(duration)


append(m1.group(), 1), append(m5.group(), 5), append(m15.group(), 15), append(m30.group(), 30)

if(otc == "s"):
    for i in range(len(active)):
        active[i] += "-OTC"


def convert(str_date, str_hour):                                            #Função para converter a hora para timestamp
    timestamp = (f'{str_date},{str_hour}')                                  #Cria string com data e hora
    timestamp = datetime.datetime.strptime(timestamp, "%d/%m/%Y,%H:%M")     #Formata data e hora para o padrão americano
    timestamp = datetime.datetime.timestamp(timestamp)                      #Formata data e hora para timestamp
    return timestamp


def buy(active, action, expiration):  #Função para efetuar a compra (buy)

    global count, value

    check_bin,id_bin=account.buy(value, active, action, expiration)     ###BUY BINÁRIA!!!
    status = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}, {active}, {action}, {expiration}"
    print(f"\n-Binaria - Compra executada com sucesso!\n ID:{id_bin}\n {status}")
    if check_bin == True:
                         #---------- BINARIA ----------
        check_res, res = account.check_win_v3(id_bin)
        if(check_res == 'loose'): #SE valor menor que 0, EXECUTAR MARTINGALE
            print(f' Loss {active}: {res}! Fazendo Martingale...')
            check,id=account.buy(value*2.5, active, action, expiration) ###BINÁRIA!!
            statusm = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}, {active}, {action}, {expiration}"
            if (check == True):
                check_resm,resm=account.check_win_v3(id)
                print(f"--Martingale executado! Lucro: R$ {round(resm, 2)} - {statusm} \n")
            else:
                print(f"--Martingale não executado! {status}\n")

        else: #SE NAO PRECISAR DO MARTINGALE
            print(f' Win! Lucro: R$ {round(res,2)} - {status}: \n')

    else:
                            #---------- DIGITAL ----------
        cid_dig,id_dig=account.buy_digital_spot(active, value, action.lower(), expiration) ###BUY DIGITAL!!!
        status1 = (f'{active}, {action}, {expiration}')
        print(f'\n-Digital - Compra executada com sucesso!\n ID:{id_dig}\n {status1}')
        if (cid_dig):
            while True:
                rem_status,rem = account.check_win_digital_v2(id_dig)
                if(rem_status):
                    break

            if(rem < 0): ###SE PREJUÍZO, EXECUTA MARTINGALE

                print(f' Loss {active}: {rem}! Fazendo Martingale...')
                cid_dig2,id_dig2 = account.buy_digital_spot(active, value*2.5, action.lower(), expiration)
                status2 = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}, {active}, {action}, {expiration}"
                if (cid_dig2):
                    while True:
                        resma_status,resma = account.check_win_digital_v2(id_dig2)
                        if(resma_status):
                            break

                    print(f'--Martingale bem sucedido! Lucro: R$ {round(resma,2)} - {status2}: \n')

            else: ###CASO NÃO ENTRE NO MARTINGALE
                print(f" Win! Lucro: R$ {round(rem, 2)} - {status1}\n ")


    count = count + 1



def trigger(buy_time, active, action, expiration):

    while True:
        global check, reason, account
        if time.time() >= buy_time:  # Se agora é a hora de compra ou mais tarde
            try:
                buy(active, action, expiration)
                break

            except websocket.WebSocketConnectionClosedException:
                print("\nErro: Conexão falhou. Tentando reconectar...")
                while True:
                    check, reason = account.connect()
                    if check is True:
                        print('Conexão reestabelecida!')
                        sys.exit(0)
                    time.sleep(1)

        time.sleep(1)

def main():

    global count, value

    for i in range(len(sinal)):     #Roda o loop X vezes (X = quantidade de sinais)

        buy_time = convert(date[i], hour[i])        #Hora da compra menos delay da hora do sistema
        buy_time = buy_time - lag

        if (time.time() > convert(date[i], hour[i]) - lag):      #Se o horário da compra ja passou (' 15': margem de erro em segundos)
            print(f"\n{count}. Horario da compra invalido!")
            count += 1
            continue


        k = threading.Thread(target=trigger,args=(buy_time, active[i], action[i], expiration[i]))  #Cria um Thread para o respectivo sinal
        k.start()

main()



