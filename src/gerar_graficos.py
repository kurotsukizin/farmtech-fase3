from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_TRATADO = RAIZ / "data" / "leituras_tratadas.csv"
PASTA_IMAGENS = RAIZ / "images"
PASTA_DATA = RAIZ / "data"

COLUNAS_CORRELACAO = [
    "umidade_solo_simulada",
    "temperatura",
    "pH_simulado",
    "nitrogenio",
    "fosforo",
    "potassio",
    "bomba_ligada",
]


def salvar(figura, nome):
    figura.tight_layout()

    destino = PASTA_IMAGENS / nome

    figura.savefig(
        destino,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(figura)
    print(f"Grafico gerado: {destino}")


def formatar_eixo_tempo(eixo):
    localizador = mdates.AutoDateLocator()

    eixo.xaxis.set_major_locator(localizador)
    eixo.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(localizador)
    )

    eixo.grid(alpha=0.25)


def main():
    PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)

    if not ARQUIVO_TRATADO.exists():
        raise FileNotFoundError(
            "Execute primeiro src/tratamento_dados.py."
        )

    df = pd.read_csv(
        ARQUIVO_TRATADO,
        parse_dates=["data_hora"],
    )

    df = df.sort_values("data_hora")

    if df.empty:
        raise ValueError("O arquivo tratado esta vazio.")

    # 1. Umidade e media movel.
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        df["data_hora"],
        df["umidade_solo_simulada"],
        label="Umidade simulada",
        color="steelblue",
        alpha=0.65,
        linewidth=1,
    )

    ax.plot(
        df["data_hora"],
        df["umidade_media_movel_6h"],
        label="Media movel de 6 horas",
        color="navy",
        linewidth=1.6,
    )

    ax.axhline(
        60,
        color="firebrick",
        linestyle="--",
        label="Limite configurado no firmware: 60%",
    )

    ax.set(
        title="FarmTech Nexo — Umidade simulada ao longo do tempo",
        xlabel="Data simulada",
        ylabel="Umidade simulada (%)",
        ylim=(-2, 102),
    )

    formatar_eixo_tempo(ax)
    ax.legend(loc="best")

    salvar(fig, "01_umidade_media_movel.png")

    # 2. pH simulado e faixa configurada.
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        df["data_hora"],
        df["pH_simulado"],
        color="purple",
        linewidth=1.2,
        label="pH simulado pelo LDR",
    )

    ax.axhspan(
        6.0,
        6.8,
        color="green",
        alpha=0.18,
        label="Faixa configurada: 6,0 a 6,8",
    )

    ax.set(
        title="FarmTech Nexo — pH simulado ao longo do tempo",
        xlabel="Data simulada",
        ylabel="pH simulado",
        ylim=(0, 14),
    )

    formatar_eixo_tempo(ax)
    ax.legend(loc="best")

    salvar(fig, "02_ph_simulado.png")

    # 3. Estado registrado da bomba.
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.step(
        df["data_hora"],
        df["bomba_ligada"],
        where="post",
        color="darkgreen",
        linewidth=1.2,
    )

    ax.set(
        title="FarmTech Nexo — Estado registrado da bomba",
        xlabel="Data simulada",
        ylabel="Estado",
        ylim=(-0.1, 1.1),
    )

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Desligada", "Ligada"])

    formatar_eixo_tempo(ax)

    salvar(fig, "03_estado_bomba.png")

    # 4. Horas simuladas de bomba por dia.
    diario = (
        df.assign(data=df["data_hora"].dt.normalize())
        .groupby("data")
        .agg(
            registros=("bomba_ligada", "size"),
            horas_bomba_simuladas=(
                "horas_bomba_simuladas",
                "sum",
            ),
        )
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(
        diario.index,
        diario["horas_bomba_simuladas"],
        width=0.8,
        color="teal",
    )

    ax.set(
        title=(
            "FarmTech Nexo — Horas simuladas de bomba por dia\n"
            "Dias com menos de 24 registros possuem cobertura parcial"
        ),
        xlabel="Data simulada",
        ylabel="Horas simuladas com bomba ligada",
        ylim=(0, 24),
    )

    formatar_eixo_tempo(ax)

    salvar(fig, "04_bomba_por_dia.png")

    # 5. Correlacao: variaveis constantes ficam de fora,
    # pois sua correlacao nao pode ser calculada.
    numericos = df[COLUNAS_CORRELACAO].apply(
        pd.to_numeric,
        errors="coerce",
    )

    constantes = [
        coluna
        for coluna in numericos.columns
        if numericos[coluna].nunique(dropna=True) < 2
    ]

    variaveis = [
        coluna
        for coluna in numericos.columns
        if coluna not in constantes
    ]

    if len(variaveis) >= 2:
        correlacao = numericos[variaveis].corr()

        correlacao.to_csv(
            PASTA_DATA / "correlacao_sensores.csv",
            encoding="utf-8",
        )

        fig, ax = plt.subplots(figsize=(10, 8))

        imagem = ax.imshow(
            correlacao,
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
        )

        posicoes = np.arange(len(variaveis))

        ax.set_xticks(posicoes)
        ax.set_yticks(posicoes)

        ax.set_xticklabels(
            variaveis,
            rotation=45,
            ha="right",
        )

        ax.set_yticklabels(variaveis)

        for linha in range(len(variaveis)):
            for coluna in range(len(variaveis)):
                valor = correlacao.iloc[linha, coluna]

                texto = (
                    f"{valor:.2f}"
                    if pd.notna(valor)
                    else "N/D"
                )

                ax.text(
                    coluna,
                    linha,
                    texto,
                    ha="center",
                    va="center",
                    color=(
                        "white"
                        if pd.notna(valor) and abs(valor) > 0.6
                        else "black"
                    ),
                )

        ax.set_title(
            "FarmTech Nexo — Correlacao de Pearson\n"
            "Associacao nesta simulacao; nao demonstra causalidade"
        )

        fig.colorbar(
            imagem,
            ax=ax,
            label="Coeficiente de correlacao",
        )

        salvar(fig, "05_correlacao.png")

    else:
        print(
            "Correlacao nao gerada: menos de duas "
            "variaveis com variacao."
        )

    if constantes:
        print(
            "Variaveis sem variacao, excluidas da correlacao:",
            ", ".join(constantes),
        )

    print("\nGeracao dos graficos concluida.")


if __name__ == "__main__":
    main()