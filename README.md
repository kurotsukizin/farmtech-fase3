# FarmTech Solutions / Nexo — Fase 3

Projeto da FIAP que integra simulação no Wokwi, tratamento de dados em Python e persistência em PostgreSQL para acompanhar o histórico de irrigação de tomate.

## Objetivo

Simular leituras de sensores de uma plantação de tomate, armazenar o histórico em CSV, tratar os dados, gerar análises visuais e carregar as informações em um banco PostgreSQL.

A cultura utilizada é **tomate**. O manejo simulado segue a regra:

- NPK completo.
- pH entre 6,0 e 6,8.
- Umidade do solo abaixo de 60%.
- Bomba ligada somente quando todas as condições são atendidas.

## Tecnologias

- Python 3
- Pandas
- NumPy
- Matplotlib
- Wokwi
- ESP32
- PostgreSQL 18
- Psycopg 3
- pgAdmin 4

## Estrutura do projeto

```text
data/                  CSVs brutos, tratados e resumos
images/                Gráficos gerados
evidencias/            Relatório do tratamento
sql/                   Scripts de criação e consultas
src/                   Scripts Python
wokwi/                 Diagrama do circuito
.env                   Credenciais locais, não versionadas
```

## Firmware e sensores

O circuito utiliza:

- ESP32 DevKit C V4.
- DHT22 para umidade e temperatura.
- LDR para pH simulado.
- Três botões para N, P e K.
- Módulo relé para acionar a bomba.

Os sensores representam condições de forma didática. O valor do LDR é convertido em pH simulado e não mede o pH real do solo.

A bomba é ligada apenas quando:

```text
NPK completo
E pH entre 6,0 e 6,8
E umidade abaixo de 60%
```

Qualquer falha de leitura do DHT desliga a bomba por segurança.

## Execução do tratamento

Com o ambiente virtual ativado:

```bash
python src/tratamento_dados.py
```

O script gera:

- `data/leituras_tratadas.csv`
- `data/leituras_rejeitadas.csv`
- `data/resumo_diario.csv`
- `data/correlacao_sensores.csv`
- `evidencias/relatorio_tratamento.txt`

## Geração dos gráficos

```bash
python src/gerar_graficos.py
```

Os gráficos são salvos em `images/`.

## Banco PostgreSQL

Crie o banco e o usuário no pgAdmin:

```text
Banco: farmtech_fase3
Usuário: farmtech_app
```

Depois execute:

```text
sql/cria_tabelas_postgresql.sql
```

O script cria:

- `ft_cultura`
- `ft_manejo`
- `ft_leitura`

E cadastra o manejo:

```text
TOMATE_WOKWI_V1
```

## Configuração da conexão

Crie um arquivo `.env` na raiz:

```env
PGHOST=localhost
PGPORT=5432
PGDATABASE=farmtech_fase3
PGUSER=farmtech_app
PGPASSWORD=sua_senha
```

O arquivo `.env` não deve ser enviado ao GitHub.

## Carga dos dados

```bash
python src/carga_postgresql.py
```

O script lê `data/leituras_tratadas.csv` e carrega os registros em `ft_leitura`.

A carga é idempotente: registros já existentes para o mesmo manejo e horário são atualizados, não duplicados.

## Consultas gerenciais

Execute as consultas do arquivo:

```text
sql/consultas_gestao_postgresql.sql
```

Elas permitem analisar:

- Resumo geral do histórico.
- Média diária de umidade, temperatura e pH.
- Horas de bomba ligada por dia.
- Dias com maior necessidade de irrigação.
- Divergências entre bomba esperada e bomba real.
- Correlação entre sensores e acionamento da bomba.

## Resultados atuais

A base carregada contém:

```text
645 leituras aceitas

271 leituras com bomba ligada
42,02% do tempo com bomba ligada
```

Cada registro representa uma hora simulada, não uma hora real de execução do Wokwi.

## Observações

- O histórico atual não corresponde aos 2.160 registros de 90 dias planejados.
- Não há vazão definida, portanto não é calculado volume de água.
- Correlação entre variáveis não implica causalidade.
