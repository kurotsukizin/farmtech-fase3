import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVO_CSV = RAIZ_PROJETO / "data" / "leituras_tratadas.csv"

CODIGO_MANEJO = "TOMATE_WOKWI_V1"

CAMPOS_ESPERADOS = [
    "data_hora",
    "umidade_solo_simulada",
    "temperatura",
    "pH_simulado",
    "nitrogenio",
    "fosforo",
    "potassio",
    "bomba_ligada",
    "origem",
    "npk_adequado",
    "ph_adequado",
    "solo_seco",
    "bomba_esperada",
    "divergencia_bomba",
    "motivo_decisao",
    "umidade_media_movel_6h",
    "horas_bomba_simuladas",
]


def converter_inteiro(valor: str) -> int:
    return int(float(valor))


def converter_decimal(valor: str):
    valor = valor.strip()

    if valor == "":
        return None

    return float(valor.replace(",", "."))


def carregar_registros() -> list[tuple]:
    if not ARQUIVO_CSV.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CSV}")

    with ARQUIVO_CSV.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)

        if leitor.fieldnames is None:
            raise ValueError("O CSV está vazio ou não possui cabeçalho.")

        faltantes = [
            campo
            for campo in CAMPOS_ESPERADOS
            if campo not in leitor.fieldnames
        ]

        if faltantes:
            raise ValueError(f"Colunas ausentes no CSV: {faltantes}")

        registros = []

        for linha in leitor:
            registros.append((
                linha["data_hora"].strip(),
                converter_decimal(linha["umidade_solo_simulada"]),
                converter_decimal(linha["temperatura"]),
                converter_decimal(linha["pH_simulado"]),
                converter_inteiro(linha["nitrogenio"]),
                converter_inteiro(linha["fosforo"]),
                converter_inteiro(linha["potassio"]),
                converter_inteiro(linha["bomba_ligada"]),
                linha["origem"].strip(),
                converter_inteiro(linha["npk_adequado"]),
                converter_inteiro(linha["ph_adequado"]),
                converter_inteiro(linha["solo_seco"]),
                converter_inteiro(linha["bomba_esperada"]),
                converter_inteiro(linha["divergencia_bomba"]),
                linha["motivo_decisao"].strip(),
                converter_decimal(linha["umidade_media_movel_6h"]),
                converter_decimal(linha["horas_bomba_simuladas"]),
            ))

    return registros


SQL_BUSCAR_MANEJO = """
    SELECT id_manejo
    FROM ft_manejo
    WHERE codigo = %s;
"""

SQL_INSERIR_LEITURA = """
    INSERT INTO ft_leitura (
        id_manejo,
        data_hora,
        umidade_solo_simulada,
        temperatura,
        pH_simulado,
        nitrogenio,
        fosforo,
        potassio,
        bomba_ligada,
        origem,
        npk_adequado,
        ph_adequado,
        solo_seco,
        bomba_esperada,
        divergencia_bomba,
        motivo_decisao,
        umidade_media_movel_6h,
        horas_bomba_simuladas
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s
    )
    ON CONFLICT (id_manejo, data_hora)
    DO UPDATE SET
        umidade_solo_simulada = EXCLUDED.umidade_solo_simulada,
        temperatura = EXCLUDED.temperatura,
        ph_simulado = EXCLUDED.ph_simulado,
        nitrogenio = EXCLUDED.nitrogenio,
        fosforo = EXCLUDED.fosforo,
        potassio = EXCLUDED.potassio,
        bomba_ligada = EXCLUDED.bomba_ligada,
        origem = EXCLUDED.origem,
        npk_adequado = EXCLUDED.npk_adequado,
        ph_adequado = EXCLUDED.ph_adequado,
        solo_seco = EXCLUDED.solo_seco,
        bomba_esperada = EXCLUDED.bomba_esperada,
        divergencia_bomba = EXCLUDED.divergencia_bomba,
        motivo_decisao = EXCLUDED.motivo_decisao,
        umidade_media_movel_6h = EXCLUDED.umidade_media_movel_6h,
        horas_bomba_simuladas = EXCLUDED.horas_bomba_simuladas;
"""


def main() -> None:
    load_dotenv(RAIZ_PROJETO / ".env")

    configuracao = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }

    if not all([
        configuracao["dbname"],
        configuracao["user"],
        configuracao["password"],
    ]):
        raise ValueError(
            "Preencha PGDATABASE, PGUSER e PGPASSWORD no arquivo .env."
        )

    registros = carregar_registros()

    if not registros:
        print("Nenhum registro encontrado no CSV tratado.")
        return

    print(f"Registros lidos do CSV: {len(registros)}")

    with psycopg.connect(**configuracao) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(SQL_BUSCAR_MANEJO, (CODIGO_MANEJO,))
            resultado = cursor.fetchone()

            if resultado is None:
                raise ValueError(
                    f"Manejo não encontrado: {CODIGO_MANEJO}"
                )

            id_manejo = resultado[0]

            inseridos = 0

            for registro in registros:
                valores = (id_manejo, *registro)
                cursor.execute(SQL_INSERIR_LEITURA, valores)
                inseridos += 1

        conexao.commit()

    print(f"Registros processados no PostgreSQL: {inseridos}")
    print("Carga concluída.")


if __name__ == "__main__":
    main()