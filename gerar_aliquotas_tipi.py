import pandas as pd
from pathlib import Path

# ============================
# CONFIGURAÇÕES GERAIS
# ============================

# Arquivos de entrada
ARQ_TIPI = Path("TIPI_IBS_CBS.xlsx")            # sua base usada pelo app
ARQ_CCLASS = Path("classificacao_tributaria.xlsx")  # planilha oficial de cClassTrib

# Arquivo de saída (recomendo gerar um novo na primeira vez)
ARQ_SAIDA = Path("TIPI_IBS_CBS_atualizada.xlsx")

# Alíquotas padrão estimadas (ajustáveis)
ALIQ_PADRAO_IBS = 17.71   # IBS cheio (%)
ALIQ_PADRAO_CBS = 8.84    # CBS cheia (%)

# ============================
# CARGA DAS BASES
# ============================

if not ARQ_TIPI.exists():
    raise FileNotFoundError(f"Não encontrei o arquivo base TIPI: {ARQ_TIPI}")

if not ARQ_CCLASS.exists():
    raise FileNotFoundError(f"Não encontrei a classificação tributária: {ARQ_CCLASS}")

print(f"Lendo TIPI: {ARQ_TIPI}")
df_tipi = pd.read_excel(ARQ_TIPI, dtype=str)
df_tipi.columns = [c.strip().upper() for c in df_tipi.columns]

# Garante a coluna do cClassTrib
if "CCLASSTRIB" not in df_tipi.columns:
    raise ValueError("A planilha TIPI_IBS_CBS.xlsx precisa ter a coluna 'CCLASSTRIB'.")

print(f"Lendo classificação tributária: {ARQ_CCLASS}")
df_cls = pd.read_excel(ARQ_CCLASS, sheet_name="Classificação Tributária")

# Normaliza nomes de colunas
df_cls.columns = [c.strip() for c in df_cls.columns]

col_cod_cclass = "Código da Classificação Tributária"
col_red_ibs = "Percentual Redução IBS"
col_red_cbs = "Percentual Redução CBS"

for col in [col_cod_cclass, col_red_ibs, col_red_cbs]:
    if col not in df_cls.columns:
        raise ValueError(f"Coluna '{col}' não encontrada em classificacao_tributaria.xlsx")

# ============================
# CÁLCULO DAS ALÍQUOTAS
# ============================

# Trabalhar com cópia enxuta da classificação
df_cclass = df_cls[[col_cod_cclass, col_red_ibs, col_red_cbs, "Tipo de Alíquota"]].copy()

# Normaliza tipos
df_cclass[col_cod_cclass] = df_cclass[col_cod_cclass].astype(str).str.strip()
df_cclass[col_red_ibs] = pd.to_numeric(df_cclass[col_red_ibs], errors="coerce").fillna(0.0)
df_cclass[col_red_cbs] = pd.to_numeric(df_cclass[col_red_cbs], errors="coerce").fillna(0.0)
df_cclass["Tipo de Alíquota"] = df_cclass["Tipo de Alíquota"].astype(str).str.strip()

def calcular_aliquotas(row):
    """
    Calcula alíquota IBS/CBS efetiva a partir de:
      - ALIQ_PADRAO_IBS / ALIQ_PADRAO_CBS
      - Percentual Redução IBS/CBS
    Regras:
      - Redução 0% → alíquota cheia
      - Redução 60% → 40% da alíquota cheia
      - Redução 100% → alíquota 0
    """
    red_ibs = float(row[col_red_ibs])
    red_cbs = float(row[col_red_cbs])

    fator_ibs = 1.0 - (red_ibs / 100.0)
    fator_cbs = 1.0 - (red_cbs / 100.0)

    aliq_ibs = ALIQ_PADRAO_IBS * fator_ibs
    aliq_cbs = ALIQ_PADRAO_CBS * fator_cbs

    # Arredondamento suave para 4 casas, depois você pode formatar com 2
    aliq_ibs = round(aliq_ibs, 4)
    aliq_cbs = round(aliq_cbs, 4)

    # Exemplo de tratamento específico opcional:
    # se quiser zerar monofásicas, pode usar a coluna "Monofásica" ou "Tributação Monofásica Normal"
    # tipo = row["Tipo de Alíquota"]
    # if "Monofásica" in tipo:
    #     aliq_ibs = 0.0
    #     aliq_cbs = 0.0

    return pd.Series({"ALIQ_IBS_CALC": aliq_ibs, "ALIQ_CBS_CALC": aliq_cbs})

print("Calculando alíquotas teóricas para cada cClassTrib...")
df_cclass[["ALIQ_IBS_CALC", "ALIQ_CBS_CALC"]] = df_cclass.apply(calcular_aliquotas, axis=1)

# ============================
# MERGE TIPI x CLASSIFICAÇÃO
# ============================

# Normaliza TIPI para merge
df_tipi["CCLASSTRIB"] = df_tipi["CCLASSTRIB"].astype(str).str.strip()

# Faz o merge TIPI (NCM) x classificação (cClassTrib)
df_merge = df_tipi.merge(
    df_cclass[[col_cod_cclass, "ALIQ_IBS_CALC", "ALIQ_CBS_CALC"]],
    how="left",
    left_on="CCLASSTRIB",
    right_on=col_cod_cclass,
)

# Se já existirem colunas ALIQ_IBS / ALIQ_CBS, sobrescreve
df_merge["ALIQ_IBS"] = df_merge["ALIQ_IBS_CALC"]
df_merge["ALIQ_CBS"] = df_merge["ALIQ_CBS_CALC"]

# Remove colunas auxiliares
df_merge.drop(columns=[col_cod_cclass, "ALIQ_IBS_CALC", "ALIQ_CBS_CALC"], inplace=True)

# ============================
# GRAVAÇÃO DA NOVA BASE
# ============================

print(f"Gravando planilha atualizada: {ARQ_SAIDA}")
df_merge.to_excel(ARQ_SAIDA, index=False)

print("\nConcluído.")
print(f"- Linhas TIPI: {len(df_tipi)}")
print(f"- Linhas TIPI com cClassTrib encontrado: {df_merge['ALIQ_IBS'].notna().sum()}")
print(f"- Arquivo gerado: {ARQ_SAIDA.resolve()}")
print("\nAgora você pode substituir o TIPI_IBS_CBS.xlsx do app por esse arquivo atualizado.")
