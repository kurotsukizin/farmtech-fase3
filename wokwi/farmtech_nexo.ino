#include <DHT.h>
#include <math.h>
#include <time.h>

#define PINO_DHT 4
#define PINO_LDR 34
#define PINO_N 14
#define PINO_P 27
#define PINO_K 26
#define PINO_RELE 25

#define UMIDADE_LIMITE 60.0
#define PH_MINIMO 6.0
#define PH_MAXIMO 6.8

#define INTERVALO_MS 200
#define EPOCH_INICIAL 1767225600LL
#define SEGUNDOS_POR_CICLO 3600

DHT dht(PINO_DHT, DHT22);

long long timestampAtual = EPOCH_INICIAL;
unsigned long ultimoCiclo = 0;
unsigned long contadorCiclos = 0;

void setup() {
  Serial.begin(115200);

  pinMode(PINO_N, INPUT_PULLUP);
  pinMode(PINO_P, INPUT_PULLUP);
  pinMode(PINO_K, INPUT_PULLUP);
  pinMode(PINO_RELE, OUTPUT);

  digitalWrite(PINO_RELE, HIGH);

  dht.begin();

  Serial.println("FarmTech Nexo - Tomate");
  Serial.println("data_hora,umidade_solo_simulada,temperatura,pH_simulado,nitrogenio,fosforo,potassio,bomba_ligada,origem");
}

void loop() {
  unsigned long agora = millis();

  if (agora - ultimoCiclo < INTERVALO_MS) {
    return;
  }

  ultimoCiclo = agora;
  contadorCiclos++;

  float umidade = dht.readHumidity();
  float temperatura = dht.readTemperature();

  int leituraLdr = analogRead(PINO_LDR);
  float ph = leituraLdr * 14.0 / 4095.0;

  bool nitrogenio = digitalRead(PINO_N) == LOW;
  bool fosforo = digitalRead(PINO_P) == LOW;
  bool potassio = digitalRead(PINO_K) == LOW;

  bool npkCompleto = nitrogenio && fosforo && potassio;
  bool phAdequado = ph >= PH_MINIMO && ph <= PH_MAXIMO;
  bool soloSeco = umidade < UMIDADE_LIMITE;

  bool dhtValido = !isnan(umidade) && !isnan(temperatura);
  bool bombaLigada = false;

  if (!dhtValido) {
    bombaLigada = false;
    Serial.println("Falha na leitura do DHT22. Bomba desligada por seguranca.");
  } else if (!npkCompleto) {
    bombaLigada = false;
    Serial.println("NPK incompleto. Bomba desligada.");
  } else if (!phAdequado) {
    bombaLigada = false;
    Serial.println("pH fora da faixa adequada. Bomba desligada.");
  } else if (!soloSeco) {
    bombaLigada = false;
    Serial.println("Umidade adequada. Bomba desligada.");
  } else {
    bombaLigada = true;
    Serial.println("Condicoes adequadas. Bomba ligada.");
  }

  digitalWrite(PINO_RELE, bombaLigada ? LOW : HIGH);

  char dataHora[25];
  time_t momento = (time_t)timestampAtual;
  struct tm tempoUtc;
  gmtime_r(&momento, &tempoUtc);
  strftime(dataHora, sizeof(dataHora), "%Y-%m-%d %H:%M:%S", &tempoUtc);

  Serial.printf(
    "%s,%.2f,%.2f,%.2f,%d,%d,%d,%d,Wokwi\n",
    dataHora,
    umidade,
    temperatura,
    ph,
    nitrogenio ? 1 : 0,
    fosforo ? 1 : 0,
    potassio ? 1 : 0,
    bombaLigada ? 1 : 0
  );

  timestampAtual += SEGUNDOS_POR_CICLO;

  if (contadorCiclos >= 2160) {
    Serial.println("Historico de 90 dias concluido.");
    while (true) {
      delay(1000);
    }
  }
}