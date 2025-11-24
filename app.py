import os
import re
import time
import datetime
import requests
from collections import defaultdict

import pandas as pd
from tkinter import Tk, filedialog, messagebox

# ==========================
#   CONFIGURAÇÕES GERAIS
# ==========================

URL_BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1/"

# ==========================
#   FUNÇÕES AUXILIARES
# ==========================

def only_digits(s: str) -> str:
    return re.sub(r"[^0-9]", "", s or "")


def format_cnpj_mask(cnpj: str) -> str:
    c = only_digits(cnpj)
    if len(c) != 14:
        return cnpj
    return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def normalizar_situacao_cadastral(txt: str) -> str:
    s = (txt or "").strip().upper()
    if not s:
        return "N/A"
    if "ATIV" in s:
        return "ATIVO"
    if "INAPT" in s:
        return "INAPTO"
    if "SUSP" in s:
        return "SUSPENSO"
    if "BAIX" in s:
        return "BAIXADO"
    return s


def classificar_tipo_operacao_por_cfop(cfop: str) -> str:
    """
    Classifica a linha como PRODUTO ou SERVIÇO a partir do CFOP:
      - grupo 3 ou 4 (segundo dígito) => SERVIÇO (transporte/comunicação)
      - demais => PRODUTO
    """
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return "DESCONHECIDO"
    grupo = cfop[1]
    if grupo in {"3", "4"}:
        return "SERVIÇO"
    return "PRODUTO"


def sugerir_cclasstrib_2026(cfop: str) -> str:
    """
    Sugestão de cClassTrib 2026 com base na natureza do CFOP.
    REGRAS (simplificadas, alinhadas com a lógica que você já vem usando):
      - CFOP de saída/prestação (5, 6, 7) com grupos 1,3,4,5,6,7 => 000001 (operações onerosas)
      - CFOP de devolução (grupo 2) => 000001 (mas idealmente seguir o cClassTrib da nota original)
      - CFOP grupo 9 (remessas diversas: garantia, brinde, etc.) => 410999 (operações não onerosas genéricas)
      - Demais => 000001 (fallback)
    """
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return "000001"

    primeiro = cfop[0]
    grupo = cfop[1]

    # Só faz sentido cClassTrib para NF emitida (5,6,7)
    if primeiro not in {"5", "6", "7"}:
        return "000001"

    # Casos especiais já definidos por você (entrega futura e remessa)
    if cfop in {"5922", "6922", "7922", "5923", "6923", "7923"}:
        return "000001"
    if cfop in {"5116", "6116", "7116", "5117", "6117", "7117"}:
        return "000001"

    if grupo in {"1", "3", "4", "5", "6", "7"}:
        return "000001"  # venda / prestação onerosa
    if grupo == "2":
        return "000001"  # devoluções – usar o mesmo cClassTrib da original
    if grupo == "9":
        return "410999"  # operações não onerosas (garantia, teste, brinde, etc.)

    return "000001"


def observacao_cclasstrib(cfop: str) -> str:
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return ""
    primeiro = cfop[0]
    grupo = cfop[1]

    if primeiro in {"5", "6", "7"} and grupo == "2":
        return "Devolução: idealmente usar o mesmo cClassTrib da nota fiscal original."
    if primeiro in {"5", "6", "7"} and grupo == "9":
        return "Provável operação não onerosa (garantia/bonificação/teste). Revisar caso a caso."
    return ""


# ==========================
#   CONSULTA CNPJ / CNAE
# ==========================

def consulta_brasilapi_cnpj(cnpj_limpo: str) -> dict:
    try:
        r = requests.get(f"{URL_BRASILAPI_CNPJ}{cnpj_limpo}", timeout=15)
        if r.status_code in (400, 404):
            return {"__error": "not_found"}
        if r.status_code in (429, 500, 502, 503, 504):
            return {"__error": "unavailable"}
        r.raise_for_status()
        return r.json()
    except:
        return {"__error": "unavailable"}


def enriquecer_com_cnpj(cnpj_raw: str) -> dict:
    """
    Recebe CNPJ do SPED (0000), consulta BrasilAPI,
    devolve dict com CNAE e dados essenciais.
    """
    cnpj_limpo = only_digits(cnpj_raw)
    if len(cnpj_limpo) != 14:
        return {"cnpj": cnpj_raw, "__error": "cnpj_invalido"}

    dados = consulta_brasilapi_cnpj(cnpj_limpo)
    if dados.get("__error"):
        return {"cnpj": cnpj_limpo, "__error": dados["__error"]}

    sit = normalizar_situacao_cadastral(dados.get("descricao_situacao_cadastral", ""))

    perfil = {
        "CNPJ": format_cnpj_mask(dados.get("cnpj", cnpj_limpo)),
        "Razao_Social": dados.get("razao_social", ""),
        "Nome_Fantasia": dados.get("nome_fantasia", ""),
        "Situacao_Cadastral": sit,
        "Data_Inicio_Atividade": dados.get("data_inicio_atividade", ""),
        "CNAE_Fiscal_Codigo": dados.get("cnae_fiscal", ""),
        "CNAE_Fiscal_Descricao": dados.get("cnae_fiscal_descricao", ""),
        "Porte": dados.get("porte", ""),
        "Natureza_Juridica": dados.get("natureza_juridica", ""),
        "Email": dados.get("email", ""),
        "Municipio": dados.get("municipio", ""),
        "UF": dados.get("uf", ""),
        "CEP": dados.get("cep", ""),
        "Data_Consulta": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return perfil


# ==========================
#   LEITURA DO SPED ICMS/IPI
# ==========================

def processar_sped_icms(caminho_arquivo: str):
    """
    Lê SPED ICMS/IPI (.txt), extrai:
      - Dados do contribuinte (0000)
      - Cadastro de produtos (0200)
      - Itens de nota (C170)
    Retorna:
      master_data (0000 + CNPJ enriquecido),
      df_itens (C170 com NCM/CFOP),
    """
    master_data = {}
    produtos_0200 = {}  # cod_item -> {descr, ncm}
    itens = []

    with open(caminho_arquivo, "r", encoding="latin-1") as f:
        for linha in f:
            linha = linha.rstrip("\n")
            if not linha.startswith("|"):
                continue

            partes = linha.split("|")
            if len(partes) < 2:
                continue

            registro = partes[1]

            # 0000 - dados do contribuinte
            if registro == "0000":
                # |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|CPF|UF|IE|COD_MUN|IM|SUFRAMA|IND_PERFIL|IND_ATIV|
                master_data["COD_VER"] = partes[2] if len(partes) > 2 else ""
                master_data["COD_FIN"] = partes[3] if len(partes) > 3 else ""
                master_data["DT_INI"] = partes[4] if len(partes) > 4 else ""
                master_data["DT_FIN"] = partes[5] if len(partes) > 5 else ""
                master_data["NOME"] = partes[6] if len(partes) > 6 else ""
                master_data["CNPJ"] = partes[7] if len(partes) > 7 else ""
                master_data["UF"] = partes[9] if len(partes) > 9 else ""
                master_data["IE"] = partes[10] if len(partes) > 10 else ""

            # 0200 - cadastro de produtos
            if registro == "0200":
                # |0200|COD_ITEM|DESCR_ITEM|UNID_INV|TIPO_ITEM|COD_NCM|EX_IPI|COD_GEN|COD_LST|ALIQ_ICMS|
                cod_item = partes[2] if len(partes) > 2 else ""
                descr_item = partes[3] if len(partes) > 3 else ""
                ncm = partes[6] if len(partes) > 6 else ""
                produtos_0200[cod_item] = {
                    "COD_ITEM": cod_item,
                    "DESCR_ITEM": descr_item,
                    "NCM": ncm,
                }

            # C170 - itens de notas
            if registro == "C170":
                # |C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC|IND_MOV|CST_ICMS|CFOP|...|
                if len(partes) < 12:
                    continue

                cod_item = partes[3]
                descr_compl = partes[4]
                try:
                    vl_item = float((partes[6] or "0").replace(",", "."))
                except ValueError:
                    vl_item = 0.0
                cfop = partes[11] if len(partes) > 11 else ""

                item = {
                    "COD_ITEM": cod_item,
                    "DESCR_COMPL": descr_compl,
                    "VL_ITEM": vl_item,
                    "CFOP": cfop,
                }

                if cod_item in produtos_0200:
                    item["DESCR_ITEM"] = produtos_0200[cod_item]["DESCR_ITEM"]
                    item["NCM"] = produtos_0200[cod_item]["NCM"]
                else:
                    item["DESCR_ITEM"] = ""
                    item["NCM"] = ""

                itens.append(item)

    df_itens = pd.DataFrame(itens)
    if df_itens.empty:
        raise ValueError("Nenhum registro C170 encontrado no arquivo SPED.")

    # Adiciona classificação de operação e cClassTrib
    df_itens["TIPO_OPERACAO"] = df_itens["CFOP"].astype(str).apply(classificar_tipo_operacao_por_cfop)

    # cClassTrib focado nas saídas (5, 6, 7)
    df_itens["cClassTrib_2026"] = df_itens["CFOP"].astype(str).apply(sugerir_cclasstrib_2026)
    df_itens["OBS_2026"] = df_itens["CFOP"].astype(str).apply(observacao_cclasstrib)

    # Enriquecimento CNPJ/CNAE
    cnpj_sped = master_data.get("CNPJ", "")
    perfil_cnpj = enriquecer_com_cnpj(cnpj_sped)

    master_data_enriquecido = {
        **master_data,
        **{
            "CNPJ_FORMATADO": perfil_cnpj.get("CNPJ", format_cnpj_mask(cnpj_sped)),
            "RAZAO_SOCIAL_CNPJ": perfil_cnpj.get("Razao_Social", ""),
            "NOME_FANTASIA_CNPJ": perfil_cnpj.get("Nome_Fantasia", ""),
            "SITUACAO_CADASTRAL_CNPJ": perfil_cnpj.get("Situacao_Cadastral", ""),
            "CNAE_FISCAL_CODIGO": perfil_cnpj.get("CNAE_Fiscal_Codigo", ""),
            "CNAE_FISCAL_DESCRICAO": perfil_cnpj.get("CNAE_Fiscal_Descricao", ""),
            "PORTE": perfil_cnpj.get("Porte", ""),
            "NATUREZA_JURIDICA": perfil_cnpj.get("Natureza_Juridica", ""),
            "DATA_INICIO_ATIVIDADE": perfil_cnpj.get("Data_Inicio_Atividade", ""),
        },
    }

    return master_data_enriquecido, df_itens


# ==========================
#   AGREGAÇÕES / RELATÓRIOS
# ==========================

def gerar_relatorios(master_data: dict, df_itens: pd.DataFrame, caminho_sped: str) -> str:
    """
    Gera Excel com:
      - DADOS_EMPRESA_2025
      - RANKING_PRODUTOS_NCM_CFOP
      - PERFIL_TRIB_2026
      - RANKING_CFOP
    """
    pasta = os.path.dirname(caminho_sped)
    nome_base = os.path.splitext(os.path.basename(caminho_sped))[0]
    caminho_saida = os.path.join(pasta, f"Diagnostico_Tributario_2025_2026_{nome_base}.xlsx")

    # Foco em operações de saída/prestação (CFOP 5,6,7)
    df_saidas = df_itens[df_itens["CFOP"].astype(str).str[0].isin(["5", "6", "7"])].copy()

    # Ranking produtos por NCM + CFOP
    df_rank_prod = (
        df_saidas.groupby(["NCM", "CFOP", "DESCR_ITEM"], dropna=False, as_index=False)["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    # Ranking CFOP
    df_rank_cfop = (
        df_saidas.groupby("CFOP", as_index=False)["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    # Perfil tributário 2026: NCM + CFOP + Tipo + cClassTrib
    df_perfil_2026 = (
        df_saidas.groupby(
            ["NCM", "CFOP", "DESCR_ITEM", "TIPO_OPERACAO", "cClassTrib_2026", "OBS_2026"],
            dropna=False,
            as_index=False,
        )["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    total_receita = df_perfil_2026["VL_ITEM"].sum()
    if total_receita == 0:
        total_receita = 1
    df_perfil_2026["PERCENTUAL_RECEITA"] = (df_perfil_2026["VL_ITEM"] / total_receita) * 100

    # Dados empresa em DataFrame
    df_empresa = pd.DataFrame([master_data])

    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df_empresa.to_excel(writer, sheet_name="DADOS_EMPRESA_2025", index=False)
        df_rank_prod.to_excel(writer, sheet_name="RANKING_PRODUTOS_NCM_CFOP", index=False)
        df_perfil_2026.to_excel(writer, sheet_name="PERFIL_TRIB_2026", index=False)
        df_rank_cfop.to_excel(writer, sheet_name="RANKING_CFOP", index=False)

    return caminho_saida


# ==========================
#   INTERFACE TKINTER
# ==========================

def escolher_arquivo_sped() -> str:
    root = Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo SPED ICMS/IPI (.txt)",
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
    )
    root.destroy()
    return caminho


def main():
    try:
        caminho_sped = escolher_arquivo_sped()
        if not caminho_sped:
            messagebox.showwarning("Aviso", "Nenhum arquivo SPED selecionado.")
            return

        master_data, df_itens = processar_sped_icms(caminho_sped)
        caminho_excel = gerar_relatorios(master_data, df_itens, caminho_sped)

        msg = (
            f"Processamento concluído!\n\n"
            f"Arquivo SPED: {caminho_sped}\n"
            f"Excel gerado em:\n{caminho_excel}\n\n"
            f"Abas geradas:\n"
            f"- DADOS_EMPRESA_2025 (SPED + CNPJ + CNAE)\n"
            f"- RANKING_PRODUTOS_NCM_CFOP (saídas 5/6/7)\n"
            f"- PERFIL_TRIB_2026 (NCM, CFOP, Tipo, cClassTrib, valor, %)\n"
            f"- RANKING_CFOP\n"
        )
        messagebox.showinfo("Sucesso", msg)

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main()
