"""
Módulo de Coleta Automática de Dados Fiscais
=============================================

Captura e armazena dados de XMLs (NFe/NFSe) de forma discreta para análise de mercado.
Acesso restrito ao usuário Admin via painel administrativo.

Autor: PRICETAX Intelligence System
Data: 2026-01-28
"""

import os
import csv
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import hashlib


def get_brasilia_timestamp() -> str:
    """Retorna timestamp atual no fuso horário de Brasília (GMT-3)."""
    brasilia_tz = timezone(timedelta(hours=-3))
    return datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S")


def hash_cnpj(cnpj: str) -> str:
    """
    Gera hash SHA-256 de um CNPJ para anonimização (opcional).
    
    Args:
        cnpj: CNPJ em texto plano
        
    Returns:
        Hash SHA-256 do CNPJ (primeiros 12 caracteres)
    """
    if not cnpj:
        return ""
    return hashlib.sha256(cnpj.encode()).hexdigest()[:12]


def save_nfe_data(
    dados_xml: Dict[str, Any],
    usuario: str,
    anonimizar: bool = False
) -> bool:
    """
    Salva dados de NFe em arquivo CSV para análise posterior.
    
    Args:
        dados_xml: Dicionário com dados parseados do XML (de parse_nfe_xml)
        usuario: Usuário que fez upload do XML
        anonimizar: Se True, aplica hash nos CNPJs
        
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        # Criar diretório de dados se não existir
        data_dir = "logs"
        os.makedirs(data_dir, exist_ok=True)
        
        data_file = os.path.join(data_dir, "xml_nfe_data.csv")
        
        # Verificar se arquivo existe para decidir se escreve cabeçalho
        file_exists = os.path.isfile(data_file)
        
        # Timestamp da captura
        timestamp = get_brasilia_timestamp()
        
        # Extrair dados do emitente e destinatário
        emitente = dados_xml.get('emitente', {})
        destinatario = dados_xml.get('destinatario', {})
        data_emissao = dados_xml.get('data_emissao', '')
        
        # CNPJs (com ou sem anonimização)
        cnpj_emitente = hash_cnpj(emitente.get('cnpj', '')) if anonimizar else emitente.get('cnpj', '')
        cnpj_destinatario = hash_cnpj(destinatario.get('cnpj', '')) if anonimizar else destinatario.get('cnpj', '')
        
        # Processar cada item da nota
        itens = dados_xml.get('itens', [])
        
        with open(data_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp_captura',
                'usuario',
                'data_emissao',
                'cnpj_emitente',
                'razao_emitente',
                'uf_emitente',
                'cnpj_destinatario',
                'razao_destinatario',
                'uf_destinatario',
                'tipo_operacao',  # ENTRADA ou SAIDA
                'ncm',
                'cfop',
                'descricao_produto',
                'valor_unitario',
                'quantidade',
                'valor_total',
                'cst_icms',
                'vbc_icms',
                'vicms',
                'cst_pis',
                'vbc_pis',
                'vpis',
                'cst_cofins',
                'vbc_cofins',
                'vcofins',
                'cst_ibscbs',
                'cclasstrib',
                'vbc_ibscbs',
                'pibs',
                'vibs',
                'pcbs',
                'vcbs'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Escrever cabeçalho se arquivo novo
            if not file_exists:
                writer.writeheader()
            
            # Escrever cada item
            for item in itens:
                # Determinar tipo de operação pelo CFOP
                cfop = item.get('cfop', '')
                if cfop and cfop[0] in ('5', '6', '7'):
                    tipo_operacao = 'SAIDA'
                elif cfop and cfop[0] in ('1', '2', '3'):
                    tipo_operacao = 'ENTRADA'
                else:
                    tipo_operacao = 'INDEFINIDO'
                
                row = {
                    'timestamp_captura': timestamp,
                    'usuario': usuario,
                    'data_emissao': data_emissao,
                    'cnpj_emitente': cnpj_emitente,
                    'razao_emitente': emitente.get('razao_social', ''),
                    'uf_emitente': emitente.get('uf', ''),
                    'cnpj_destinatario': cnpj_destinatario,
                    'razao_destinatario': destinatario.get('razao_social', ''),
                    'uf_destinatario': destinatario.get('uf', ''),
                    'tipo_operacao': tipo_operacao,
                    'ncm': item.get('ncm', ''),
                    'cfop': cfop,
                    'descricao_produto': item.get('descricao', '')[:100],  # Limitar tamanho
                    'valor_unitario': item.get('valor_unitario', 0.0),
                    'quantidade': item.get('quantidade', 0.0),
                    'valor_total': item.get('valor_total', 0.0),
                    'cst_icms': item.get('cst_icms', ''),
                    'vbc_icms': item.get('vbc_icms', 0.0),
                    'vicms': item.get('vicms', 0.0),
                    'cst_pis': item.get('cst_pis', ''),
                    'vbc_pis': item.get('vbc_pis', 0.0),
                    'vpis': item.get('vpis', 0.0),
                    'cst_cofins': item.get('cst_cofins', ''),
                    'vbc_cofins': item.get('vbc_cofins', 0.0),
                    'vcofins': item.get('vcofins', 0.0),
                    'cst_ibscbs': item.get('cst_ibscbs', ''),
                    'cclasstrib': item.get('cclasstrib', ''),
                    'vbc_ibscbs': item.get('vbc_ibscbs', 0.0),
                    'pibs': item.get('pibs', 0.0),
                    'vibs': item.get('vibs', 0.0),
                    'pcbs': item.get('pcbs', 0.0),
                    'vcbs': item.get('vcbs', 0.0)
                }
                
                writer.writerow(row)
        
        return True
        
    except Exception as e:
        print(f"Erro ao salvar dados de NFe: {e}")
        return False


def save_nfse_data(
    dados_xml: Dict[str, Any],
    usuario: str,
    anonimizar: bool = False
) -> bool:
    """
    Salva dados de NFSe em arquivo CSV para análise posterior.
    
    Args:
        dados_xml: Dicionário com dados parseados do XML de NFSe
        usuario: Usuário que fez upload do XML
        anonimizar: Se True, aplica hash nos CNPJs
        
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        # Criar diretório de dados se não existir
        data_dir = "logs"
        os.makedirs(data_dir, exist_ok=True)
        
        data_file = os.path.join(data_dir, "xml_nfse_data.csv")
        
        # Verificar se arquivo existe para decidir se escreve cabeçalho
        file_exists = os.path.isfile(data_file)
        
        # Timestamp da captura
        timestamp = get_brasilia_timestamp()
        
        # Extrair dados do prestador e tomador
        prestador = dados_xml.get('prestador', {})
        tomador = dados_xml.get('tomador', {})
        servico = dados_xml.get('servico', {})
        
        # CNPJs (com ou sem anonimização)
        cnpj_prestador = hash_cnpj(prestador.get('cnpj', '')) if anonimizar else prestador.get('cnpj', '')
        cnpj_tomador = hash_cnpj(tomador.get('cnpj', '')) if anonimizar else tomador.get('cnpj', '')
        
        with open(data_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp_captura',
                'usuario',
                'data_emissao',
                'cnpj_prestador',
                'razao_prestador',
                'municipio_prestador',
                'uf_prestador',
                'cnpj_tomador',
                'razao_tomador',
                'municipio_tomador',
                'uf_tomador',
                'nbs',  # Código do serviço (NBS)
                'descricao_servico',
                'valor_servico',
                'aliquota_iss',
                'valor_iss',
                'aliquota_ibs',
                'valor_ibs',
                'aliquota_cbs',
                'valor_cbs',
                'cclasstrib'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Escrever cabeçalho se arquivo novo
            if not file_exists:
                writer.writeheader()
            
            row = {
                'timestamp_captura': timestamp,
                'usuario': usuario,
                'data_emissao': dados_xml.get('data_emissao', ''),
                'cnpj_prestador': cnpj_prestador,
                'razao_prestador': prestador.get('razao_social', ''),
                'municipio_prestador': prestador.get('municipio', ''),
                'uf_prestador': prestador.get('uf', ''),
                'cnpj_tomador': cnpj_tomador,
                'razao_tomador': tomador.get('razao_social', ''),
                'municipio_tomador': tomador.get('municipio', ''),
                'uf_tomador': tomador.get('uf', ''),
                'nbs': servico.get('nbs', ''),
                'descricao_servico': servico.get('descricao', '')[:200],
                'valor_servico': servico.get('valor', 0.0),
                'aliquota_iss': servico.get('aliquota_iss', 0.0),
                'valor_iss': servico.get('valor_iss', 0.0),
                'aliquota_ibs': servico.get('aliquota_ibs', 0.0),
                'valor_ibs': servico.get('valor_ibs', 0.0),
                'aliquota_cbs': servico.get('aliquota_cbs', 0.0),
                'valor_cbs': servico.get('valor_cbs', 0.0),
                'cclasstrib': servico.get('cclasstrib', '')
            }
            
            writer.writerow(row)
        
        return True
        
    except Exception as e:
        print(f"Erro ao salvar dados de NFSe: {e}")
        return False


def get_nfe_statistics() -> Dict[str, Any]:
    """
    Retorna estatísticas agregadas dos dados de NFe capturados.
    
    Returns:
        Dict com estatísticas: total_registros, total_valor, ncms_top, etc.
    """
    try:
        data_file = "logs/xml_nfe_data.csv"
        
        if not os.path.isfile(data_file):
            return {
                'total_registros': 0,
                'total_valor': 0.0,
                'message': 'Nenhum dado capturado ainda'
            }
        
        import pandas as pd
        df = pd.read_csv(data_file)
        
        stats = {
            'total_registros': len(df),
            'total_valor': df['valor_total'].sum(),
            'total_notas': df.groupby(['cnpj_emitente', 'data_emissao']).ngroups,
            'ncms_unicos': df['ncm'].nunique(),
            'cfops_unicos': df['cfop'].nunique(),
            'ufs_origem': df['uf_emitente'].nunique(),
            'ufs_destino': df['uf_destinatario'].nunique(),
            'periodo_inicio': df['data_emissao'].min(),
            'periodo_fim': df['data_emissao'].max()
        }
        
        return stats
        
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Erro ao calcular estatísticas'
        }
