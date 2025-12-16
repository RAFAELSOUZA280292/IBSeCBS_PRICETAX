"""
Integração silenciosa com Google Sheets para armazenamento de dados de mercado.
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any

# ID da planilha do Google Sheets
SPREADSHEET_ID = "1MpzO2szc_9w1DiBNEOEJcNgsPZpTAxalvbxLjRB0m4o"

def get_google_sheets_client():
    """
    Cria cliente autenticado do Google Sheets usando credenciais do Streamlit Secrets.
    """
    try:
        # Credenciais armazenadas em st.secrets
        credentials_dict = st.secrets["gcp_service_account"]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        # Falha silenciosa
        return None

def inicializar_planilha():
    """
    Inicializa a planilha com cabeçalhos se necessário.
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
        
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Verificar se já tem cabeçalhos
        primeira_linha = sheet.row_values(1)
        
        if not primeira_linha or len(primeira_linha) == 0:
            # Criar cabeçalhos
            headers = [
                "Data_Hora_Upload",
                "Data_Emissao_NFe",
                "CNPJ_Emitente",
                "Razao_Social_Emitente",
                "UF_Emitente",
                "CNPJ_Destinatario",
                "Razao_Social_Destinatario",
                "UF_Destinatario",
                "NCM",
                "CFOP",
                "Descricao_Produto",
                "Quantidade",
                "Valor_Unitario",
                "Valor_Total",
                "CST_ICMS",
                "CST_PIS",
                "CST_COFINS",
                "BC_ICMS",
                "Valor_ICMS",
                "BC_PIS",
                "Valor_PIS",
                "BC_COFINS",
                "Valor_COFINS"
            ]
            sheet.append_row(headers)
        
        return True
    except:
        return False

def salvar_dados_xml(dados_xml: Dict[str, Any]) -> bool:
    """
    Salva dados do XML processado no Google Sheets de forma silenciosa.
    
    Args:
        dados_xml: Dicionário com dados extraídos do XML
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
        
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Data/hora atual do upload
        data_hora_upload = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Dados do emitente e destinatário
        emitente = dados_xml.get('emitente', {})
        destinatario = dados_xml.get('destinatario', {})
        data_emissao = dados_xml.get('data_emissao', '')
        
        # Processar cada item
        itens = dados_xml.get('itens', [])
        
        rows_to_add = []
        for item in itens:
            row = [
                data_hora_upload,
                data_emissao,
                emitente.get('cnpj', ''),
                emitente.get('razao_social', ''),
                emitente.get('uf', ''),
                destinatario.get('cnpj', ''),
                destinatario.get('razao_social', ''),
                destinatario.get('uf', ''),
                item.get('ncm', ''),
                item.get('cfop', ''),
                item.get('descricao', ''),
                item.get('quantidade', 0),
                item.get('valor_unitario', 0),
                item.get('valor_total', 0),
                item.get('cst_icms', ''),
                item.get('cst_pis', ''),
                item.get('cst_cofins', ''),
                item.get('vbc_icms', 0),
                item.get('vicms', 0),
                item.get('vbc_pis', 0),
                item.get('vpis', 0),
                item.get('vbc_cofins', 0),
                item.get('vcofins', 0),
            ]
            rows_to_add.append(row)
        
        # Adicionar todas as linhas de uma vez (mais eficiente)
        if rows_to_add:
            sheet.append_rows(rows_to_add)
        
        return True
    except:
        # Falha silenciosa - usuário nunca saberá
        return False
