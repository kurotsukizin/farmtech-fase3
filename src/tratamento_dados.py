from pathlib import Path

import numpy as np
import pandas as pd


# Os caminhos partem da localizacao deste script.
RAIZ = Path(__file__).resolve().parents[1]

PASTA_DATA = RAIZ / "data"
PASTA_EVIDENCIAS = RAIZ / "evidencias"

ARQUIVO_BRUTO = PASTA_DATA / "leituras_brutas.csv"
ARQUIVO_TRATADO = PASTA_DATA / "leituras_tratadas.csv"
ARQUIVO_REJEITADOS = PASTA_DATA / "leituras_rejeitadas.csv"
ARQUIVO_RESUMO_DIARIO = PASTA_DATA / "resumo_diario.csv"
ARQUIVO_RELATORIO = PASTA_EVIDENCIAS / "relatorio_tratamento.txt"

COLUNAS = [
    "data_hora",
    "umidade_solo_simulada",
    "temperatura",
    "ph_simulado",
    "nitrogenio",
    "fosforo",
    "potassio",
    "bomba_ligada",
    "origem",
]

COLUNAS_NUMERICAS = [
    "umidade_solo_simulada",
    "temperatura",
    "ph_simulado",
    "nitrogenio",
    "fosforo",
    "potassio",
    "bomba_ligada",
]

COLUNAS_BINARIAS = [
    "nitrogenio",
    "fosforo",
    "potassio",
    "bomba_ligada",
]


def main():
    PASTA_DATA.mkdir(parents=True, exist_ok=True)
    PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)

    if not ARQUIVO_BRUTO.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_BRUTO}"
        )

    dados = pd.read_csv(ARQUIVO_BRUTO)

    dados.columns = dados.columns.str.strip()

    faltantes = sorted(set(COLUNAS) - set(dados.columns))

    if faltantes:
        raise ValueError(
            f"Colunas obrigatorias ausentes: {faltantes}"
        )

    total_original = len(dados)

    if total_original == 0:
        raise ValueError("O arquivo bruto nao possui leituras.")

    # Copia para validacao, preservando o arquivo de origem.
    df = dados[COLUNAS].copy()

    df["data_hora"] = pd.to_datetime(
        df["data_hora"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce",
        )

    df["origem"] = (
        df["origem"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    # Regras estruturais e de dominio.
    # Temperaturas extremas nao sao excluidas apenas
    # por parecerem incomuns para a cultura simulada.
    regras = pd.DataFrame(index=df.index)

    regras["campo_ausente_ou_invalido"] = (
        df[COLUNAS].isna().any(axis=1)
    )

    regras["umidade_fora_da_faixa"] = (
        df["umidade_solo_simulada"].notna()
        & ~df["umidade_solo_simulada"].between(0, 100)
    )

    regras["ph_fora_da_faixa"] = (
        df["pH_simulado"].notna()
        & ~df["pH_simulado"].between(0, 14)
    )

    for coluna in COLUNAS_BINARIAS:
        regras[f"{coluna}_nao_binario"] = (
            df[coluna].notna()
            & ~df[coluna].isin([0, 1])
        )

    valores_numericos = df[COLUNAS_NUMERICAS].to_numpy(
        dtype=float
    )

    regras["valor_infinito"] = np.isinf(
        valores_numericos
    ).any(axis=1)

    invalidas = regras.any(axis=1)

    # Duplicatas sao identificadas entre registros validos.
    # Para este conjunto de uma unica estacao, a chave e a data.
    duplicadas = pd.Series(False, index=df.index)

    duplicadas.loc[~invalidas] = (
        df.loc[~invalidas, "data_hora"]
        .duplicated(keep="first")
    )

    regras["data_hora_duplicada"] = duplicadas

    rejeitar = regras.any(axis=1)

    # Exporta os valores originais rejeitados e seus motivos.
    rejeitados = dados.loc[rejeitar].copy()

    rejeitados["motivo_rejeicao"] = regras.loc[
        rejeitar
    ].apply(
        lambda linha: ";".join(
            linha.index[linha.to_numpy(dtype=bool)]
        ),
        axis=1,
    )

    rejeitados.to_csv(
        ARQUIVO_REJEITADOS,
        index=False,
        encoding="utf-8",
    )

    df = (
        df.loc[~rejeitar]
        .sort_values("data_hora")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError(
            "Nenhuma leitura valida. Consulte "
            "data/leituras_rejeitadas.csv."
        )

    for coluna in COLUNAS_BINARIAS:
        df[coluna] = df[coluna].astype("int8")

    # Indicadores derivados da logica original do firmware.
    df["npk_adequado"] = (
        df[["nitrogenio", "fosforo", "potassio"]]
        .eq(1)
        .all(axis=1)
        .astype("int8")
    )

    df["ph_adequado"] = (
        df["pH_simulado"]
        .between(6.0, 6.8)
        .astype("int8")
    )

    df["solo_seco"] = (
        df["umidade_solo_simulada"]
        .lt(60.0)
        .astype("int8")
    )

    df["bomba_esperada"] = (
        df["npk_adequado"].eq(1)
        & df["ph_adequado"].eq(1)
        & df["solo_seco"].eq(1)
    ).astype("int8")

    # Divergencias sao sinalizadas, nunca corrigidas
    # automaticamente no estado registrado da bomba.
    df["divergencia_bomba"] = (
        df["bomba_ligada"]
        .ne(df["bomba_esperada"])
        .astype("int8")
    )

    # Mesma prioridade de decisao do firmware original.
    df["motivo_decisao"] = np.select(
        [
            df["npk_adequado"].eq(0),
            df["ph_adequado"].eq(0),
            df["solo_seco"].eq(1),
        ],
        [
            "npk_incompleto",
            "ph_fora_da_faixa",
            "condicoes_para_irrigar",
        ],
        default="umidade_suficiente",
    )

    # Media movel temporal das seis horas anteriores,
    # incluindo o instante atual.
    serie_umidade = df.set_index(
        "data_hora"
    )["umidade_solo_simulada"]

    df["umidade_media_movel_6h"] = (
        serie_umidade
        .rolling("6h", min_periods=1)
        .mean()
        .to_numpy()
        .round(2)
    )

    diferencas = df["data_hora"].diff()

    intervalos_irregulares = int(
        diferencas.iloc[1:].ne(
            pd.Timedelta(hours=1)
        ).sum()
    )

    # Cada linha do firmware representa uma hora simulada.
    # Nao corresponde a tempo real de funcionamento.
    df["horas_bomba_simuladas"] = (
        df["bomba_ligada"].astype(float)
    )

    resumo_diario = (
        df.assign(data=df["data_hora"].dt.date)
        .groupby("data", as_index=False)
        .agg(
            registros=("data_hora", "size"),
            umidade_media=(
                "umidade_solo_simulada",
                "mean",
            ),
            temperatura_media=("temperatura", "mean"),
            ph_medio=("pH_simulado", "mean"),
            horas_bomba_simuladas=(
                "horas_bomba_simuladas",
                "sum",
            ),
            divergencias=("divergencia_bomba", "sum"),
        )
    )

    resumo_diario = resumo_diario.round(2)

    df.to_csv(
        ARQUIVO_TRATADO,
        index=False,
        encoding="utf-8",
        date_format="%Y-%m-%d %H:%M:%S",
    )

    resumo_diario.to_csv(
        ARQUIVO_RESUMO_DIARIO,
        index=False,
        encoding="utf-8",
    )

    percentual_ligada = (
        df["bomba_ligada"].mean() * 100
    )

    relatorio = "\n".join([
        "FARMTECH NEXO - TRATAMENTO DE DADOS",
        "",
        f"Registros recebidos: {total_original}",
        f"Registros rejeitados: {int(rejeitar.sum())}",
        f"Registros tratados: {len(df)}",
        f"Inicio: {df['data_hora'].min()}",
        f"Ultima leitura: {df['data_hora'].max()}",
        f"Intervalos diferentes de 1 hora: "
        f"{intervalos_irregulares}",
        f"Leituras com bomba ligada: "
        f"{int(df['bomba_ligada'].sum())}",
        f"Percentual de leituras com bomba ligada: "
        f"{percentual_ligada:.2f}%",
        f"Horas de bomba simuladas: "
        f"{df['horas_bomba_simuladas'].sum():.0f}",
        f"Divergencias na regra da bomba: "
        f"{int(df['divergencia_bomba'].sum())}",
        "",
        "Observacoes:",
        "- O arquivo bruto nao foi alterado.",
        "- Nao foram criadas leituras sinteticas.",
        "- Nao houve preenchimento automatico de lacunas.",
        "- pH e umidade do solo sao representacoes didaticas.",
        "- Horas simuladas nao equivalem a horas reais.",
        "- Dias inicial e final podem ter coleta parcial.",
    ])

    ARQUIVO_RELATORIO.write_text(
        relatorio,
        encoding="utf-8",
    )

    print(relatorio)
    print("\nArquivos gerados:")
    print(ARQUIVO_TRATADO)
    print(ARQUIVO_REJEITADOS)
    print(ARQUIVO_RESUMO_DIARIO)
    print(ARQUIVO_RELATORIO)


if __name__ == "__main__":
    main()