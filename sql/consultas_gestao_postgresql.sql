-- =============================================================
-- FarmTech Solutions / Nexo - Fase 3
-- Consultas gerenciais em PostgreSQL
-- Banco: farmtech_fase3
-- Manejo: TOMATE_WOKWI_V1
-- =============================================================


-- 1. Resumo geral do histórico de irrigação
SELECT
    c.nome AS cultura,
    m.codigo AS manejo,
    COUNT(l.id_leitura) AS total_leituras,
    MIN(l.data_hora) AS primeira_leitura,
    MAX(l.data_hora) AS ultima_leitura,
    ROUND(AVG(l.umidade_solo_simulada)::numeric, 2) AS umidade_media,
    ROUND(MIN(l.umidade_solo_simulada)::numeric, 2) AS umidade_minima,
    ROUND(MAX(l.umidade_solo_simulada)::numeric, 2) AS umidade_maxima,
    ROUND(AVG(l.ph_simulado)::numeric, 2) AS ph_medio,
    SUM(l.bomba_ligada) AS horas_bomba_ligada,
    ROUND(
        100.0 * SUM(l.bomba_ligada) / NULLIF(COUNT(l.id_leitura), 0),
        2
    ) AS percentual_bomba_ligada
FROM ft_cultura c
JOIN ft_manejo m
    ON m.id_cultura = c.id_cultura
LEFT JOIN ft_leitura l
    ON l.id_manejo = m.id_manejo
GROUP BY
    c.nome,
    m.codigo
ORDER BY
    c.nome,
    m.codigo;


-- 2. Resumo diário: umidade, temperatura, pH e bomba
SELECT
    DATE(l.data_hora) AS data_leitura,
    COUNT(*) AS total_leituras,
    ROUND(AVG(l.umidade_solo_simulada)::numeric, 2) AS umidade_media,
    ROUND(MIN(l.umidade_solo_simulada)::numeric, 2) AS umidade_minima,
    ROUND(MAX(l.umidade_solo_simulada)::numeric, 2) AS umidade_maxima,
    ROUND(AVG(l.temperatura)::numeric, 2) AS temperatura_media,
    ROUND(AVG(l.ph_simulado)::numeric, 2) AS ph_medio,
    SUM(l.bomba_ligada) AS horas_bomba_ligada,
    SUM(l.divergencia_bomba) AS leituras_com_divergencia
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
GROUP BY DATE(l.data_hora)
ORDER BY data_leitura;


-- 3. Dias com maior tempo de bomba ligada
SELECT
    DATE(l.data_hora) AS data_leitura,
    SUM(l.bomba_ligada) AS horas_bomba_ligada,
    ROUND(AVG(l.umidade_solo_simulada)::numeric, 2) AS umidade_media
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
GROUP BY DATE(l.data_hora)
ORDER BY
    horas_bomba_ligada DESC,
    data_leitura ASC
LIMIT 10;


-- 4. Leituras com divergência entre bomba esperada e bomba real
SELECT
    l.data_hora,
    l.umidade_solo_simulada,
    l.ph_simulado,
    l.nitrogenio,
    l.fosforo,
    l.potassio,
    l.bomba_esperada,
    l.bomba_ligada,
    l.motivo_decisao
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
  AND l.divergencia_bomba = 1
ORDER BY l.data_hora;


-- 5. Distribuição das decisões da bomba
SELECT
    l.bomba_ligada AS bomba_esteve_ligada,
    COUNT(*) AS total_leituras,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentual
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
GROUP BY l.bomba_ligada
ORDER BY l.bomba_ligada;


-- 6. Motivos mais frequentes da decisão
SELECT
    l.motivo_decisao,
    COUNT(*) AS total_leituras,
    SUM(l.bomba_ligada) AS bomba_ligada,
    SUM(l.divergencia_bomba) AS divergencias
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
GROUP BY l.motivo_decisao
ORDER BY total_leituras DESC;


-- 7. Correlação entre umidade, pH e estado da bomba
SELECT
    ROUND(
        CORR(l.umidade_solo_simulada::double precision,
             l.bomba_ligada::double precision)::numeric,
        4
    ) AS correlacao_umidade_bomba,
    ROUND(
        CORR(l.ph_simulado::double precision,
             l.bomba_ligada::double precision)::numeric,
        4
    ) AS correlacao_ph_bomba,
    ROUND(
        CORR(l.temperatura::double precision,
             l.bomba_ligada::double precision)::numeric,
        4
    ) AS correlacao_temperatura_bomba
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1';


-- 8. Comparação entre leituras com e sem NPK adequado
SELECT
    l.npk_adequado,
    COUNT(*) AS total_leituras,
    ROUND(AVG(l.umidade_solo_simulada)::numeric, 2) AS umidade_media,
    ROUND(AVG(l.ph_simulado)::numeric, 2) AS ph_medio,
    SUM(l.bomba_ligada) AS horas_bomba_ligada,
    ROUND(
        100.0 * SUM(l.bomba_ligada) / NULLIF(COUNT(*), 0),
        2
    ) AS percentual_bomba_ligada
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
GROUP BY l.npk_adequado
ORDER BY l.npk_adequado;


-- 9. Últimas 24 leituras registradas
SELECT
    l.data_hora,
    l.umidade_solo_simulada,
    l.temperatura,
    l.ph_simulado,
    l.nitrogenio,
    l.fosforo,
    l.potassio,
    l.bomba_ligada,
    l.motivo_decisao
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
ORDER BY l.data_hora DESC
LIMIT 24;


-- 10. Média móvel de umidade nas últimas 6 leituras
SELECT
    l.data_hora,
    l.umidade_solo_simulada,
    ROUND(
        AVG(l.umidade_solo_simulada) OVER (
            ORDER BY l.data_hora
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        )::numeric,
        4
    ) AS umidade_media_movel_6_leituras,
    l.bomba_ligada
FROM ft_leitura l
JOIN ft_manejo m
    ON m.id_manejo = l.id_manejo
WHERE m.codigo = 'TOMATE_WOKWI_V1'
ORDER BY l.data_hora;