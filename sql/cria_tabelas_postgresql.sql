BEGIN;

CREATE TABLE ft_cultura (
    id_cultura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT
);

CREATE TABLE ft_manejo (
    id_manejo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cultura BIGINT NOT NULL
        REFERENCES ft_cultura(id_cultura),

    codigo VARCHAR(60) NOT NULL UNIQUE,
    descricao TEXT,

    umidade_minima NUMERIC(5,2) NOT NULL
        CHECK (umidade_minima BETWEEN 0 AND 100),

    ph_minimo NUMERIC(4,2) NOT NULL,
    ph_maximo NUMERIC(4,2) NOT NULL,

    exige_npk SMALLINT NOT NULL
        CHECK (exige_npk IN (0, 1)),

    intervalo_simulado_h NUMERIC(10,4) NOT NULL
        CHECK (intervalo_simulado_h > 0),

    CONSTRAINT ck_manejo_ph
        CHECK (
            ph_minimo BETWEEN 0 AND 14
            AND ph_maximo BETWEEN 0 AND 14
            AND ph_minimo <= ph_maximo
        )
);

CREATE TABLE ft_leitura (
    id_leitura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    id_manejo BIGINT NOT NULL
        REFERENCES ft_manejo(id_manejo),

    data_hora TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,

    umidade_solo_simulada NUMERIC(5,2) NOT NULL
        CHECK (umidade_solo_simulada BETWEEN 0 AND 100),

    temperatura NUMERIC(6,2) NOT NULL,

    ph_simulado NUMERIC(4,2) NOT NULL
        CHECK (ph_simulado BETWEEN 0 AND 14),

    nitrogenio SMALLINT NOT NULL
        CHECK (nitrogenio IN (0, 1)),

    fosforo SMALLINT NOT NULL
        CHECK (fosforo IN (0, 1)),

    potassio SMALLINT NOT NULL
        CHECK (potassio IN (0, 1)),

    bomba_ligada SMALLINT NOT NULL
        CHECK (bomba_ligada IN (0, 1)),

    origem VARCHAR(50) NOT NULL,

    npk_adequado SMALLINT NOT NULL
        CHECK (npk_adequado IN (0, 1)),

    ph_adequado SMALLINT NOT NULL
        CHECK (ph_adequado IN (0, 1)),

    solo_seco SMALLINT NOT NULL
        CHECK (solo_seco IN (0, 1)),

    bomba_esperada SMALLINT NOT NULL
        CHECK (bomba_esperada IN (0, 1)),

    divergencia_bomba SMALLINT NOT NULL
        CHECK (divergencia_bomba IN (0, 1)),

    motivo_decisao TEXT NOT NULL,

    umidade_media_movel_6h NUMERIC(7,4)
        CHECK (umidade_media_movel_6h BETWEEN 0 AND 100),

    horas_bomba_simuladas NUMERIC(10,4) NOT NULL
        CHECK (horas_bomba_simuladas >= 0),

    data_carga TIMESTAMP WITH TIME ZONE NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_leitura_manejo_data
        UNIQUE (id_manejo, data_hora)
);

INSERT INTO ft_cultura (nome, descricao)
VALUES (
    'Tomate',
    'Cultura utilizada na simulacao didatica FarmTech Nexo.'
);

INSERT INTO ft_manejo (
    id_cultura,
    codigo,
    descricao,
    umidade_minima,
    ph_minimo,
    ph_maximo,
    exige_npk,
    intervalo_simulado_h
)
SELECT
    id_cultura,
    'TOMATE_WOKWI_V1',
    'NPK completo, pH entre 6.0 e 6.8 e umidade abaixo de 60%.',
    60.00,
    6.00,
    6.80,
    1,
    1.0000
FROM ft_cultura
WHERE nome = 'Tomate';

COMMIT;