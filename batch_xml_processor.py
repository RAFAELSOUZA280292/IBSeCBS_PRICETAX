"""
Processamento em Lote de XMLs NFe
==================================

Módulo para processar até 500 XMLs simultaneamente com validação completa,
geração de relatório Excel profissional e integração com data_collector (espião).

Autor: PRICETAX
Data: 06/02/2026
"""

import os
import zipfile
import tempfile
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from io import BytesIO

# Importar módulos existentes
from xml_parser import parse_nfe_xml
from data_collector import save_nfe_data


def extract_zip_to_temp(zip_file) -> Tuple[str, List[str]]:
    """
    Extrai arquivo ZIP para diretório temporário e retorna lista de XMLs.
    
    Args:
        zip_file: Arquivo ZIP do Streamlit
        
    Returns:
        Tupla (diretório temporário, lista de caminhos de XMLs)
    """
    temp_dir = tempfile.mkdtemp(prefix="pricetax_batch_")
    xml_files = []
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Extrair todos os arquivos
            zip_ref.extractall(temp_dir)
            
            # Buscar todos os XMLs (incluindo em subdiretórios)
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.xml'):
                        xml_files.append(os.path.join(root, file))
    
    except Exception as e:
        raise Exception(f"Erro ao extrair ZIP: {str(e)}")
    
    return temp_dir, xml_files


def validate_xml_structure(xml_path: str) -> Dict[str, Any]:
    """
    Valida estrutura básica do XML NFe.
    
    Returns:
        Dict com status e mensagem
    """
    try:
        # Tentar fazer parse
        resultado = parse_nfe_xml(xml_path)
        
        # Verificar campos obrigatórios
        if not resultado.get('emitente'):
            return {'valid': False, 'error': 'Emitente não encontrado'}
        
        if not resultado.get('destinatario'):
            return {'valid': False, 'error': 'Destinatário não encontrado'}
        
        if not resultado.get('itens') or len(resultado['itens']) == 0:
            return {'valid': False, 'error': 'Nenhum item encontrado'}
        
        return {'valid': True, 'error': None}
    
    except Exception as e:
        return {'valid': False, 'error': f'Erro no parse: {str(e)}'}


def calculate_expected_ibs_cbs(item: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula IBS/CBS esperados com base líquida (2026).
    
    Args:
        item: Dicionário com dados do item
        
    Returns:
        Dict com valores esperados
    """
    # Valores do item
    vprod = item.get('valor_total', 0.0)
    vicms = item.get('vicms', 0.0)
    vpis = item.get('vpis', 0.0)
    vcofins = item.get('vcofins', 0.0)
    
    # Base líquida (2026)
    base_liquida = vprod - vicms - vpis - vcofins
    
    # Alíquotas padrão 2026
    aliq_ibs = 0.10  # 0,1%
    aliq_cbs = 0.90  # 0,9%
    
    # Calcular valores esperados
    vibs_esperado = base_liquida * (aliq_ibs / 100)
    vcbs_esperado = base_liquida * (aliq_cbs / 100)
    
    return {
        'base_liquida': base_liquida,
        'vibs_esperado': vibs_esperado,
        'vcbs_esperado': vcbs_esperado,
        'aliq_ibs': aliq_ibs,
        'aliq_cbs': aliq_cbs
    }


def validate_ibs_cbs(item: Dict[str, Any], tolerancia: float = 0.02) -> Dict[str, Any]:
    """
    Valida se IBS/CBS do XML estão corretos.
    
    Args:
        item: Dicionário com dados do item
        tolerancia: Tolerância em reais para diferença
        
    Returns:
        Dict com status de validação
    """
    # Valores do XML
    vibs_xml = item.get('vibs', 0.0)
    vcbs_xml = item.get('vcbs', 0.0)
    
    # Calcular esperados
    esperados = calculate_expected_ibs_cbs(item)
    
    # Comparar
    diff_ibs = abs(vibs_xml - esperados['vibs_esperado'])
    diff_cbs = abs(vcbs_xml - esperados['vcbs_esperado'])
    
    ibs_ok = diff_ibs <= tolerancia
    cbs_ok = diff_cbs <= tolerancia
    
    return {
        'ibs_ok': ibs_ok,
        'cbs_ok': cbs_ok,
        'diff_ibs': diff_ibs,
        'diff_cbs': diff_cbs,
        'vibs_xml': vibs_xml,
        'vcbs_xml': vcbs_xml,
        'vibs_esperado': esperados['vibs_esperado'],
        'vcbs_esperado': esperados['vcbs_esperado'],
        'base_liquida': esperados['base_liquida']
    }


def process_single_xml(xml_path: str, save_to_collector: bool = True) -> Dict[str, Any]:
    """
    Processa um único XML com validação completa.
    
    Args:
        xml_path: Caminho do arquivo XML
        save_to_collector: Se True, salva no data_collector (espião)
        
    Returns:
        Dict com resultado do processamento
    """
    resultado = {
        'arquivo': os.path.basename(xml_path),
        'status': 'ERRO',
        'mensagem': '',
        'chave_acesso': '',
        'emitente_razao': '',
        'emitente_cnpj': '',
        'emitente_uf': '',
        'destinatario_razao': '',
        'destinatario_cnpj': '',
        'destinatario_uf': '',
        'data_emissao': '',
        'total_itens': 0,
        'itens_conformes': 0,
        'itens_divergentes': 0,
        'valor_total_nfe': 0.0,
        'validacoes': []
    }
    
    try:
        # Validar estrutura
        validacao = validate_xml_structure(xml_path)
        if not validacao['valid']:
            resultado['mensagem'] = validacao['error']
            return resultado
        
        # Parse completo
        dados = parse_nfe_xml(xml_path)
        
        # Extrair chave de acesso do nome do arquivo
        nome_arquivo = os.path.basename(xml_path)
        if len(nome_arquivo) >= 44:
            chave = nome_arquivo[:44]
            if chave.isdigit():
                resultado['chave_acesso'] = chave
        
        # Dados gerais
        resultado['emitente_razao'] = dados['emitente'].get('razao_social', '')
        resultado['emitente_cnpj'] = dados['emitente'].get('cnpj', '')
        resultado['emitente_uf'] = dados['emitente'].get('uf', '')
        resultado['destinatario_razao'] = dados['destinatario'].get('razao_social', '')
        resultado['destinatario_cnpj'] = dados['destinatario'].get('cnpj', '')
        resultado['destinatario_uf'] = dados['destinatario'].get('uf', '')
        resultado['data_emissao'] = dados.get('data_emissao', '')
        resultado['total_itens'] = len(dados['itens'])
        
        # Validar cada item
        itens_conformes = 0
        itens_divergentes = 0
        valor_total = 0.0
        
        for idx, item in enumerate(dados['itens'], 1):
            valor_total += item.get('valor_total', 0.0)
            
            # Validar IBS/CBS
            validacao_item = validate_ibs_cbs(item)
            
            if validacao_item['ibs_ok'] and validacao_item['cbs_ok']:
                itens_conformes += 1
                status_item = 'CONFORME'
            else:
                itens_divergentes += 1
                status_item = 'DIVERGENTE'
            
            resultado['validacoes'].append({
                'item': idx,
                'ncm': item.get('ncm', ''),
                'cfop': item.get('cfop', ''),
                'descricao': item.get('descricao', ''),
                'valor': item.get('valor_total', 0.0),
                'status': status_item,
                'ibs_xml': validacao_item['vibs_xml'],
                'ibs_esperado': validacao_item['vibs_esperado'],
                'diff_ibs': validacao_item['diff_ibs'],
                'cbs_xml': validacao_item['vcbs_xml'],
                'cbs_esperado': validacao_item['vcbs_esperado'],
                'diff_cbs': validacao_item['diff_cbs'],
                'base_liquida': validacao_item['base_liquida']
            })
        
        resultado['itens_conformes'] = itens_conformes
        resultado['itens_divergentes'] = itens_divergentes
        resultado['valor_total_nfe'] = valor_total
        
        # Status geral
        if itens_divergentes == 0:
            resultado['status'] = 'CONFORME'
            resultado['mensagem'] = f'Todos os {itens_conformes} itens estão corretos'
        else:
            resultado['status'] = 'DIVERGENTE'
            resultado['mensagem'] = f'{itens_divergentes} de {resultado["total_itens"]} itens com divergência'
        
        # Salvar no data_collector (espião)
        if save_to_collector:
            try:
                save_nfe_data(dados, usuario="BatchProcessor", anonimizar=False)
            except Exception as e:
                # Não falhar o processamento se o espião falhar
                print(f"Aviso: Erro ao salvar no data_collector: {e}")
        
    except Exception as e:
        resultado['mensagem'] = f'Erro: {str(e)}'
        resultado['status'] = 'ERRO'
    
    return resultado


def process_batch(xml_files: List[str], save_to_collector: bool = True, 
                  progress_callback=None) -> List[Dict[str, Any]]:
    """
    Processa lote de XMLs.
    
    Args:
        xml_files: Lista de caminhos de XMLs
        save_to_collector: Se True, salva no data_collector
        progress_callback: Função para atualizar progresso (opcional)
        
    Returns:
        Lista de resultados
    """
    resultados = []
    total = len(xml_files)
    
    for idx, xml_path in enumerate(xml_files, 1):
        resultado = process_single_xml(xml_path, save_to_collector)
        resultados.append(resultado)
        
        # Callback de progresso
        if progress_callback:
            progress_callback(idx, total, resultado['arquivo'])
    
    return resultados


def generate_summary_stats(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Gera estatísticas resumidas do processamento.
    
    Returns:
        Dict com estatísticas
    """
    total = len(resultados)
    conformes = sum(1 for r in resultados if r['status'] == 'CONFORME')
    divergentes = sum(1 for r in resultados if r['status'] == 'DIVERGENTE')
    erros = sum(1 for r in resultados if r['status'] == 'ERRO')
    
    total_itens = sum(r['total_itens'] for r in resultados)
    itens_conformes = sum(r['itens_conformes'] for r in resultados)
    itens_divergentes = sum(r['itens_divergentes'] for r in resultados)
    
    valor_total = sum(r['valor_total_nfe'] for r in resultados)
    
    return {
        'total_xmls': total,
        'xmls_conformes': conformes,
        'xmls_divergentes': divergentes,
        'xmls_erros': erros,
        'percentual_conformes': (conformes / total * 100) if total > 0 else 0,
        'total_itens': total_itens,
        'itens_conformes': itens_conformes,
        'itens_divergentes': itens_divergentes,
        'valor_total': valor_total,
        'data_processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }


def generate_excel_report(resultados: List[Dict[str, Any]]) -> BytesIO:
    """
    Gera relatório Excel profissional com 4 abas.
    
    Returns:
        BytesIO com arquivo Excel
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # ABA 1: RESUMO
        stats = generate_summary_stats(resultados)
        df_resumo = pd.DataFrame([
            ['Total de XMLs Processados', stats['total_xmls']],
            ['XMLs Conformes', stats['xmls_conformes']],
            ['XMLs com Divergências', stats['xmls_divergentes']],
            ['XMLs com Erros', stats['xmls_erros']],
            ['% Conformidade', f"{stats['percentual_conformes']:.2f}%"],
            ['', ''],
            ['Total de Itens', stats['total_itens']],
            ['Itens Conformes', stats['itens_conformes']],
            ['Itens Divergentes', stats['itens_divergentes']],
            ['', ''],
            ['Valor Total (R$)', f"{stats['valor_total']:,.2f}"],
            ['', ''],
            ['Data do Processamento', stats['data_processamento']]
        ], columns=['Métrica', 'Valor'])
        df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
        
        # ABA 2: VALIDAÇÃO (todos os XMLs)
        df_validacao = pd.DataFrame([{
            'Arquivo': r['arquivo'],
            'Status': r['status'],
            'Chave Acesso': r['chave_acesso'],
            'Emitente': r['emitente_razao'],
            'CNPJ Emitente': r['emitente_cnpj'],
            'UF Emitente': r['emitente_uf'],
            'Destinatário': r['destinatario_razao'],
            'CNPJ Destinatário': r['destinatario_cnpj'],
            'UF Destinatário': r['destinatario_uf'],
            'Data Emissão': r['data_emissao'],
            'Total Itens': r['total_itens'],
            'Itens Conformes': r['itens_conformes'],
            'Itens Divergentes': r['itens_divergentes'],
            'Valor Total (R$)': r['valor_total_nfe'],
            'Mensagem': r['mensagem']
        } for r in resultados])
        df_validacao.to_excel(writer, sheet_name='Validação', index=False)
        
        # ABA 3: DIVERGÊNCIAS (apenas XMLs com problemas)
        divergentes = [r for r in resultados if r['status'] in ['DIVERGENTE', 'ERRO']]
        if divergentes:
            df_divergencias = pd.DataFrame([{
                'Arquivo': r['arquivo'],
                'Status': r['status'],
                'Chave Acesso': r['chave_acesso'],
                'Emitente': r['emitente_razao'],
                'Destinatário': r['destinatario_razao'],
                'Itens Divergentes': r['itens_divergentes'],
                'Valor Total (R$)': r['valor_total_nfe'],
                'Mensagem': r['mensagem']
            } for r in divergentes])
            df_divergencias.to_excel(writer, sheet_name='Divergências', index=False)
        
        # ABA 4: DADOS COMPLETOS (detalhamento por item)
        dados_completos = []
        for r in resultados:
            for val in r['validacoes']:
                dados_completos.append({
                    'Arquivo': r['arquivo'],
                    'Chave Acesso': r['chave_acesso'],
                    'Emitente': r['emitente_razao'],
                    'Destinatário': r['destinatario_razao'],
                    'Item': val['item'],
                    'NCM': val['ncm'],
                    'CFOP': val['cfop'],
                    'Descrição': val['descricao'],
                    'Valor Item (R$)': val['valor'],
                    'Base Líquida (R$)': val['base_liquida'],
                    'IBS XML (R$)': val['ibs_xml'],
                    'IBS Esperado (R$)': val['ibs_esperado'],
                    'Dif. IBS (R$)': val['diff_ibs'],
                    'CBS XML (R$)': val['cbs_xml'],
                    'CBS Esperado (R$)': val['cbs_esperado'],
                    'Dif. CBS (R$)': val['diff_cbs'],
                    'Status': val['status']
                })
        
        if dados_completos:
            df_completo = pd.DataFrame(dados_completos)
            df_completo.to_excel(writer, sheet_name='Dados Completos', index=False)
    
    output.seek(0)
    return output
