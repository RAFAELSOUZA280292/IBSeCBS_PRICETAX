import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import zipfile, os, re
from pathlib import Path
from functools import lru_cache

# =========================
# Utils
# =========================

def only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # Caso "1.234,56"
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    for raw in (dt_ini or "", dt_fin or ""):
        dig = only_digits(raw)
        if len(dig) == 8:
            return f"{dig[2:4]}/{dig[4:8]}"
    return ""

def coletar_txts(paths):
    txts = []
    for p in paths:
        p = Path(p)
        if p.is_file() and p.suffix.lower() == ".zip":
            tmp = p.parent / (p.stem + "_unzipped")
            tmp.mkdir(exist_ok=True)
            with zipfile.ZipFile(p, "r") as z:
                z.extractall(tmp)
            txts.extend(list(tmp.rglob("*.txt")))
        elif p.is_file() and p.suffix.lower() == ".txt":
            txts.append(p)
    return txts

# =========================
# TIPI / IBS-CBS DATABASE
# =========================

# Caminho padrão da base TIPI mapeada (ajuste se necessário)
TIPI_DB_PATH = Path("TIPI_2022_ATUALIZADA_MAPEAMENTO_IBS_CBS_80porcento.xlsx")
TIPI_DB_SHEET = "TIPI_NCM_IBS_CBS"

def normalizar_ncm(ncm: str) -> str:
    """
    Normaliza NCM para 8 dígitos (somente números).
    Aceita formatos: '0101.21.00', '01012100', '1012100' etc.
    """
    dig = only_digits(ncm)
    if not dig:
        return ""
    # TIPI é 8 dígitos
    return dig.zfill(8)

@lru_cache(maxsize=1)
def carregar_tipi_db() -> pd.DataFrame:
    """
    Carrega a base TIPI mapeada (NCM x IBS/CBS) como 'banco de dados'.
    Espera a aba TIPI_NCM_IBS_CBS com as colunas criadas na etapa anterior.
    """
    if not TIPI_DB_PATH.exists():
        # Não quebra o programa, só avisa e deixa a consulta em fallback
        print(f"[AVISO] Arquivo TIPI não encontrado em: {TIPI_DB_PATH}")
        return pd.DataFrame()

    df = pd.read_excel(TIPI_DB_PATH, sheet_name=TIPI_DB_SHEET, dtype=str)
    # Garante colunas mínimas
    col_obrig = ["NCM", "DESCRICAO_TIPI", "ALIQUOTA_IPI",
                 "Capitulo_TIPI", "Secao_TIPI",
                 "ID_Grupo", "Nome_Grupo",
                 "Tratamento_IBS_CBS_Geral", "Possivel_Imposto_Seletivo",
                 "Observacoes_IBS_CBS"]
    for c in col_obrig:
        if c not in df.columns:
            df[c] = ""

    # Normaliza NCM para chave de busca
    df["NCM_DIGITOS"] = df["NCM"].astype(str).apply(normalizar_ncm)
    return df

def consultar_ibscbs_por_ncm(ncm: str) -> dict:
    """
    Consulta na base TIPI → IBS/CBS um NCM específico.
    Retorna dict com campos principais ou mensagem de não encontrado.
    """
    ncm_norm = normalizar_ncm(ncm)
    if not ncm_norm:
        return {
            "encontrado": False,
            "mensagem": "NCM vazio ou inválido.",
            "NCM": ncm,
        }

    df = carregar_tipi_db()
    if df.empty:
        return {
            "encontrado": False,
            "mensagem": "Base TIPI/IBS-CBS não carregada. Verifique o caminho do arquivo.",
            "NCM": ncm,
        }

    linha = df[df["NCM_DIGITOS"] == ncm_norm].head(1)
    if linha.empty:
        return {
            "encontrado": False,
            "mensagem": "NCM não localizado na TIPI mapeada.",
            "NCM": ncm,
        }

    row = linha.iloc[0]
    return {
        "encontrado": True,
        "mensagem": "",
        "NCM": str(row.get("NCM", "")).strip(),
        "DESCRICAO_TIPI": str(row.get("DESCRICAO_TIPI", "")).strip(),
        "ALIQUOTA_IPI": str(row.get("ALIQUOTA_IPI", "")).strip(),
        "Capitulo_TIPI": str(row.get("Capitulo_TIPI", "")).strip(),
        "Secao_TIPI": str(row.get("Secao_TIPI", "")).strip(),
        "ID_Grupo": str(row.get("ID_Grupo", "")).strip(),
        "Nome_Grupo": str(row.get("Nome_Grupo", "")).strip(),
        "Tratamento_IBS_CBS_Geral": str(row.get("Tratamento_IBS_CBS_Geral", "")).strip(),
        "Possivel_Imposto_Seletivo": str(row.get("Possivel_Imposto_Seletivo", "")).strip(),
        "Observacoes_IBS_CBS": str(row.get("Observacoes_IBS_CBS", "")).strip(),
    }

# =========================
# Cabeçalhos (PVA)
# =========================

M200_HEADERS = [
    "Valor Total da Contribuição Não-cumulativa do Período",
    "Valor do Crédito Descontado, Apurado no Próprio Período da Escrituração",
    "Valor do Crédito Descontado, Apurado em Período de Apuração Anterior",
    "Valor Total da Contribuição Não Cumulativa Devida",
    "Valor Retido na Fonte Deduzido no Período (Não Cumulativo)",
    "Outras Deduções do Regime Não Cumulativo no Período",
    "Valor da Contribuição Não Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição Cumulativa do Período",
    "Valor Retido na Fonte Deduzido no Período (Cumulativo)",
    "Outras Deduções do Regime Cumulativo no Período",
    "Valor da Contribuição Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição a Recolher/Pagar no Período",
]
M600_HEADERS = M200_HEADERS[:]  # mesma estrutura visual no PVA

# =========================
# Tabelas de códigos (sementes) + loaders de CSV (opcional)
# =========================

# Tabela 4.3.5 – Código da Contribuição Social Apurada (para COD_CONT)
COD_CONT_DESC = {
    "01": "Contribuição não-cumulativa apurada à alíquota básica",
    "02": "Contribuição não-cumulativa apurada à alíquota diferenciada/reduzida",
    "03": "Contribuição não-cumulativa – receitas com alíquota específica",
    "04": "Contribuição não-cumulativa – receitas sujeitas à alíquota zero",
    "05": "Contribuição não-cumulativa – receitas não alcançadas (isenção/suspensão)",
    "06": "Contribuição não-cumulativa – regime monofásico",
    "07": "Contribuição não-cumulativa – substituição tributária",
    "08": "Contribuição não-cumulativa – alíquota por unidade de medida",
    "09": "Contribuição não-cumulativa – outras hipóteses legais",
    "12": "Contribuição cumulativa – alíquota básica",
    "13": "Contribuição cumulativa – alíquota diferenciada",
    "14": "Contribuição cumulativa – alíquota zero",
    "15": "Contribuição cumulativa – outras hipóteses legais",
    "51": "Contribuição apurada – código 51 (ajuste conforme tabela interna/guia)",
}

# Natureza da receita / CODIGO_DET (usado em M410/M810)
NAT_REC_DESC = {
    "403": "Venda de óleo combustível, tipo bunker, MF – Marine Fuel (2710.19.22), "
           "óleo combustível, tipo bunker, MGO – Marine Gás Oil (2710.19.21) e "
           "óleo combustível, tipo bunker, ODM – Óleo Diesel Marítimo (2710.19.21), "
           "quando destinados à navegação de cabotagem e de apoio portuário e marítimo",
    "309": "ZFM – Zona Franca de Manaus",
    "401": "Exportação de mercadorias para o exterior",
    "405": "Desperdícios, resíduos ou aparas de plástico, de papel ou cartão, de vidro, "
           "de ferro ou aço, de cobre, de níquel, de alumínio, de chumbo, de zinco e de estanho, "
           "e demais desperdícios e resíduos metálicos do Capítulo 81 da Tipi",
    "908": "Vendas de mercadorias destinadas ao consumo",
    "911": "Receitas financeiras, inclusive variação cambial ativa tributável",
    "999": "Código genérico – Operações tributáveis à alíquota zero/isenção/suspensão (especificar)",
}

# NAT_BC_CRED (M105/M505) – 01..21
NAT_BC_CRED_DESC = {
    "01": "Aquisição de bens para revenda",
    "02": "Aquisição de bens e serviços utilizados como insumo",
    "03": "Energia elétrica e térmica, inclusive sob forma de vapor",
    "04": "Aluguéis de prédios",
    "05": "Aluguéis de máquinas e equipamentos",
    "06": "Armazenagem de mercadoria e frete na operação de venda",
    "07": "Contraprestações de arrendamento mercantil",
    "08": "Máquinas, equipamentos e outros bens incorporados ao ativo imobilizado (depreciação)",
    "09": "Edificações e benfeitorias em imóveis próprios ou de terceiros (depreciação/amortização)",
    "10": "Devolução de vendas sujeito à incidência não-cumulativa",
    "11": "Ativos intangíveis (amortização)",
    "12": "Encargos de depreciação, amortização e contraprestações de arrendamento no custo",
    "13": "Outras operações geradoras de crédito",
    "18": "Crédito presumido",
    "19": "Fretes na aquisição de insumos e bens para revenda",
    "20": "Armazenagem, seguros e vigilância na aquisição",
    "21": "Outros créditos vinculados à atividade",
}

def carregar_csv_mapa(csv_path: Path) -> dict:
    """Carrega CSV opcional com colunas: codigo,descricao."""
    try:
        df = pd.read_csv(csv_path, dtype=str, sep=",")
        df = df.rename(columns={c: c.strip().lower() for c in df.columns})
        if not {"codigo", "descricao"}.issubset(set(df.columns)):
            return {}
        df["codigo"] = df["codigo"].astype(str).str.strip()
        df["descricao"] = df["descricao"].astype(str).str.strip()
        return {row["codigo"]: row["descricao"] for _, row in df.iterrows() if row["codigo"]}
    except Exception:
        return {}

# Sobrescreve/expande por CSVs se existirem:
COD_CONT_DESC.update(carregar_csv_mapa(Path("map_cod_cont.csv")))
NAT_REC_DESC.update(carregar_csv_mapa(Path("map_nat_rec.csv")))
NAT_BC_CRED_DESC.update(carregar_csv_mapa(Path("map_nat_bc_cred.csv")))

# Helpers de descrição/normalização
def desc_cod_cont(codigo: str) -> str:
    c = (codigo or "").strip()
    return COD_CONT_DESC.get(c, f"(Descrição não cadastrada: {c})")

def desc_nat_rec(codigo: str) -> str:
    c = (codigo or "").strip()
    return NAT_REC_DESC.get(c, f"(Descrição não cadastrada: {c})")

def norm_nat_bc(codigo: str) -> str:
    d = only_digits((codigo or "").strip())
    if not d:
        return (codigo or "").strip()
    return d.zfill(2) if len(d) == 1 else d

def desc_nat_bc(codigo: str) -> str:
    c = norm_nat_bc(codigo)
    return NAT_BC_CRED_DESC.get(c, f"(Descrição não cadastrada: {c})") if c else ""

# =========================
# Parser focado nas 8 abas
# =========================

def parse_sped_txt(path: Path):
    empresa_cnpj = ""; dt_ini = ""; dt_fin = ""; competencia = ""
    ap_pis = []; credito_pis = []; receitas_pis = []; rec_isentas_pis = []
    ap_cofins = []; credito_cofins = []; receitas_cofins = []; rec_isentas_cofins = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            if not raw or raw == "|":
                continue
            campos = raw.rstrip("\n").split("|")
            if len(campos) < 3:
                continue
            reg = (campos[1] or "").upper()

            if reg == "0000":
                datas = [c for c in campos if re.fullmatch(r"\d{8}", c or "")]
                if len(datas) >= 2:
                    dt_ini, dt_fin = datas[0], datas[1]
                else:
                    dt_ini = campos[4] if len(campos) > 4 else ""
                    dt_fin = campos[5] if len(campos) > 5 else ""
                competencia = competencia_from_dt(dt_ini, dt_fin)
                cand = [only_digits(c) for c in campos if len(only_digits(c)) == 14]
                if cand:
                    empresa_cnpj = cand[0]

            # AP PIS (M200) com cabeçalhos do PVA
            elif reg == "M200":
                row = {"ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj}
                vals = campos[2:2+len(M200_HEADERS)]
                for titulo, val in zip(M200_HEADERS, vals):
                    row[titulo] = to_float_br(val)
                ap_pis.append(row)

            # CREDITO PIS (M105)
            elif reg == "M105":
                nat = (campos[2] if len(campos) > 2 else "").strip()
                credito_pis.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "NAT_BC_CRED": nat,
                    "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                    "CST_PIS": (campos[3] if len(campos) > 3 else "").strip(),
                    "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                    "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
                })

            # RECEITAS PIS (M210)
            elif reg == "M210":
                cod = (campos[2] if len(campos) > 2 else "").strip()
                receitas_pis.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "COD_CONT": cod,
                    "DESCR_COD_CONT": desc_cod_cont(cod),
                    "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                    "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "VL_BC_PIS": to_float_br(campos[7] if len(campos) > 7 else 0),
                    "ALIQ_PIS": to_float_br(campos[8] if len(campos) > 8 else 0),
                    "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                    "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
                })

            # RECEITAS ISENTAS PIS (M410)
            elif reg == "M410":
                nat = (campos[2] if len(campos) > 2 else "").strip()
                rec_isentas_pis.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "CODIGO_DET": nat,
                    "DESCR_CODIGO_DET": desc_nat_rec(nat),
                    "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
                })

            # AP COFINS (M600) com cabeçalhos do PVA
            elif reg == "M600":
                row = {"ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj}
                vals = campos[2:2+len(M600_HEADERS)]
                for titulo, val in zip(M600_HEADERS, vals):
                    row[titulo] = to_float_br(val)
                ap_cofins.append(row)

            # CREDITO COFINS (M505)
            elif reg == "M505":
                nat = (campos[2] if len(campos) > 2 else "").strip()
                credito_cofins.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "NAT_BC_CRED": nat,
                    "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                    "CST_COFINS": (campos[3] if len(campos) > 3 else "").strip(),
                    "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                    "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
                })

            # RECEITAS COFINS (M610)
            elif reg == "M610":
                cod = (campos[2] if len(campos) > 2 else "").strip()
                receitas_cofins.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "COD_CONT": cod,
                    "DESCR_COD_CONT": desc_cod_cont(cod),
                    "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                    "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "VL_BC_COFINS": to_float_br(campos[7] if len(campos) > 7 else 0),
                    "ALIQ_COFINS": to_float_br(campos[8] if len(campos) > 8 else 0),
                    "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                    "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
                })

            # RECEITAS ISENTAS COFINS (M810)
            elif reg == "M810":
                nat = (campos[2] if len(campos) > 2 else "").strip()
                rec_isentas_cofins.append({
                    "ARQUIVO": str(path), "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                    "CODIGO_DET": nat,
                    "DESCR_CODIGO_DET": desc_nat_rec(nat),
                    "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
                })

    return {
        "ap_pis": ap_pis, "credito_pis": credito_pis, "receitas_pis": receitas_pis, "rec_isentas_pis": rec_isentas_pis,
        "ap_cofins": ap_cofins, "credito_cofins": credito_cofins, "receitas_cofins": receitas_cofins, "rec_isentas_cofins": rec_isentas_cofins
    }

# =========================
# Processamento + Excel
# =========================

def processar_speds(caminhos, saida_excel):
    txts = coletar_txts(caminhos)
    if not txts:
        messagebox.showerror("Erro", "Nenhum arquivo .txt encontrado.")
        return

    ap_pis_all, cred_pis_all, rec_pis_all, rec_is_pis_all = [], [], [], []
    ap_cof_all, cred_cof_all, rec_cof_all, rec_is_cof_all = [], [], [], []

    for t in txts:
        d = parse_sped_txt(t)
        ap_pis_all.extend(d["ap_pis"]);         cred_pis_all.extend(d["credito_pis"])
        rec_pis_all.extend(d["receitas_pis"]);  rec_is_pis_all.extend(d["rec_isentas_pis"])
        ap_cof_all.extend(d["ap_cofins"]);      cred_cof_all.extend(d["credito_cofins"])
        rec_cof_all.extend(d["receitas_cofins"]); rec_is_cof_all.extend(d["rec_isentas_cofins"])

    # DataFrames
    df_ap_pis   = pd.DataFrame(ap_pis_all)
    df_cred_pis = pd.DataFrame(cred_pis_all)
    df_rec_pis  = pd.DataFrame(rec_pis_all)
    df_ri_pis   = pd.DataFrame(rec_is_pis_all)
    df_ap_cof   = pd.DataFrame(ap_cof_all)
    df_cred_cof = pd.DataFrame(cred_cof_all)
    df_rec_cof  = pd.DataFrame(rec_cof_all)
    df_ri_cof   = pd.DataFrame(rec_is_cof_all)

    # Índices auxiliares (para consulta no Excel)
    df_idx_cod_cont = pd.DataFrame(
        [{"COD_CONT": k, "DESCRICAO": v} for k, v in sorted(COD_CONT_DESC.items(), key=lambda x: x[0])]
    )
    df_idx_nat_rec = pd.DataFrame(
        [{"CODIGO_DET": k, "DESCRICAO": v} for k, v in sorted(NAT_REC_DESC.items(), key=lambda x: x[0])]
    )
    df_idx_nat_bc = pd.DataFrame(
        [{"NAT_BC_CRED": k, "DESCRICAO": v} for k, v in sorted(NAT_BC_CRED_DESC.items(), key=lambda x: x[0])]
    )

    # Também exporta o "banco de dados TIPI/IBS-CBS" como aba de apoio, se existir
    df_tipi = carregar_tipi_db()

    with pd.ExcelWriter(saida_excel, engine="openpyxl") as w:
        if not df_ap_pis.empty:    df_ap_pis.to_excel(w, sheet_name="AP PIS", index=False)
        if not df_cred_pis.empty:  df_cred_pis.to_excel(w, sheet_name="CREDITO PIS", index=False)
        if not df_rec_pis.empty:   df_rec_pis.to_excel(w, sheet_name="RECEITAS PIS", index=False)
        if not df_ri_pis.empty:    df_ri_pis.to_excel(w, sheet_name="RECEITAS ISENTAS PIS", index=False)

        if not df_ap_cof.empty:    df_ap_cof.to_excel(w, sheet_name="AP COFINS", index=False)
        if not df_cred_cof.empty:  df_cred_cof.to_excel(w, sheet_name="CREDITO COFINS", index=False)
        if not df_rec_cof.empty:   df_rec_cof.to_excel(w, sheet_name="RECEITAS COFINS", index=False)
        if not df_ri_cof.empty:    df_ri_cof.to_excel(w, sheet_name="RECEITAS ISENTAS COFINS", index=False)

        # índices de apoio
        if not df_idx_cod_cont.empty: df_idx_cod_cont.to_excel(w, sheet_name="ÍNDICE COD_CONT", index=False)
        if not df_idx_nat_rec.empty:  df_idx_nat_rec.to_excel(w, sheet_name="ÍNDICE NAT_REC", index=False)
        if not df_idx_nat_bc.empty:   df_idx_nat_bc.to_excel(w, sheet_name="ÍNDICE NAT_BC_CRED", index=False)

        # banco de dados TIPI/IBS-CBS (apoio para IBS/CBS)
        if not df_tipi.empty:
            # removo a coluna auxiliar de chave interna, se existir
            cols_tipi = [c for c in df_tipi.columns if c != "NCM_DIGITOS"]
            df_tipi[cols_tipi].to_excel(w, sheet_name="TIPI_IBS_CBS_DB", index=False)

    try:
        os.startfile(saida_excel)  # Windows
    except Exception:
        pass
    messagebox.showinfo("Concluído", f"Arquivo gerado:\n{saida_excel}")

# =========================
# GUI
# =========================

def selecionar_arquivos():
    arqs = filedialog.askopenfilenames(
        title="Selecione SPED (.txt/.zip)",
        filetypes=[("SPED EFD", "*.txt *.zip")]
    )
    if arqs:
        entrada_var.set(";".join(arqs))

def selecionar_saida():
    saida = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Planilha Excel", "*.xlsx")],
        title="Salvar como"
    )
    if saida:
        saida_var.set(saida)

def executar():
    entradas = [p for p in entrada_var.get().split(";") if p.strip()]
    saida = saida_var.get().strip()
    if not entradas:
        return messagebox.showerror("Erro", "Selecione pelo menos um arquivo.")
    if not saida:
        return messagebox.showerror("Erro", "Selecione o local de salvamento.")
    processar_speds(entradas, saida)

def consultar_ncm_gui():
    """
    Pequena função para testar o 'banco de dados' da TIPI/IBS-CBS via GUI.
    Pergunta um NCM e mostra o tratamento IBS/CBS mapeado.
    """
    ncm = simpledialog.askstring("Consulta NCM", "Informe o NCM (com ou sem pontos):")
    if not ncm:
        return
    info = consultar_ibscbs_por_ncm(ncm)
    if not info.get("encontrado"):
        return messagebox.showinfo("Consulta IBS/CBS", f"NCM: {info.get('NCM')}\n\n{info.get('mensagem')}")
    msg = (
        f"NCM: {info['NCM']}\n"
        f"Descrição TIPI: {info['DESCRICAO_TIPI']}\n"
        f"Capítulo/Seção: {info['Capitulo_TIPI']} / {info['Secao_TIPI']}\n\n"
        f"Grupo IBS/CBS: {info['ID_Grupo']} - {info['Nome_Grupo']}\n"
        f"Tratamento IBS/CBS (geral):\n{info['Tratamento_IBS_CBS_Geral']}\n\n"
        f"Possível Imposto Seletivo: {info['Possivel_Imposto_Seletivo']}\n"
        f"Obs.: {info['Observacoes_IBS_CBS']}"
    )
    messagebox.showinfo("Consulta IBS/CBS", msg)

janela = tk.Tk()
janela.title("SPED PIS/COFINS + Banco TIPI → IBS/CBS")
janela.geometry("780x380")
janela.resizable(False, False)

entrada_var = tk.StringVar(); saida_var = tk.StringVar()

tk.Label(janela, text="Arquivos SPED (.txt / .zip):").pack(pady=5)
tk.Entry(janela, textvariable=entrada_var, width=95).pack()
tk.Button(janela, text="Selecionar Arquivos", command=selecionar_arquivos).pack(pady=3)

tk.Label(janela, text="Salvar resultado como:").pack(pady=5)
tk.Entry(janela, textvariable=saida_var, width=95).pack()
tk.Button(janela, text="Escolher Local", command=selecionar_saida).pack(pady=3)

tk.Button(
    janela, text="🔍 Executar (SPED PIS/COFINS)", command=executar,
    bg="#0eb8b3", fg="white", width=32, height=2
).pack(pady=10)

tk.Button(
    janela, text="📘 Consultar IBS/CBS por NCM (TIPI)", command=consultar_ncm_gui,
    bg="#444444", fg="white", width=32, height=1
).pack(pady=5)

janela.mainloop()
