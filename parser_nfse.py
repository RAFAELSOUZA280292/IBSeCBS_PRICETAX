"""
parser_nfse.py
==============

Módulo para parsing e análise de XMLs de NFSe do Portal Nacional (SPED).

Este módulo processa XMLs de Nota Fiscal de Serviços Eletrônica (NFSe) emitidas
através do Portal Nacional, extraindo todos os campos relevantes para análise
fiscal e tributária.

Autor: PRICETAX
Data: 23 de Janeiro de 2026
Versão: 1.0

Estrutura de Dados:
-------------------
- Identificação da Nota
- Dados do Emitente
- Dados do Tomador
- Informações do Serviço
- Valores e Tributos (PIS, COFINS, IRRF, CSLL, ISSQN)
- Status e Competência

Uso:
----
```python
from parser_nfse import parse_nfse_xml, parse_multiple_nfse

# Processar um XML
nota = parse_nfse_xml("caminho/para/arquivo.xml")

# Processar múltiplos XMLs
notas = parse_multiple_nfse(["arquivo1.xml", "arquivo2.xml"])
```
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


# Namespace padrão do XML NFSe
NAMESPACE = {'nfse': 'http://www.sped.fazenda.gov.br/nfse'}


def safe_find_text(element: ET.Element, path: str, namespace: Dict[str, str] = NAMESPACE, default: str = "") -> str:
    """
    Busca um elemento XML e retorna seu texto de forma segura.
    
    Args:
        element: Elemento XML raiz
        path: Caminho XPath para o elemento desejado
        namespace: Dicionário de namespaces
        default: Valor padrão se elemento não for encontrado
    
    Returns:
        str: Texto do elemento ou valor padrão
    """
    found = element.find(path, namespace)
    return found.text.strip() if found is not None and found.text else default


def safe_find_float(element: ET.Element, path: str, namespace: Dict[str, str] = NAMESPACE, default: float = 0.0) -> float:
    """
    Busca um elemento XML e converte seu texto para float de forma segura.
    
    Args:
        element: Elemento XML raiz
        path: Caminho XPath para o elemento desejado
        namespace: Dicionário de namespaces
        default: Valor padrão se elemento não for encontrado ou conversão falhar
    
    Returns:
        float: Valor numérico ou valor padrão
    """
    text = safe_find_text(element, path, namespace, "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """
    Converte string de data/hora ISO 8601 para objeto datetime.
    
    Args:
        dt_string: String no formato ISO 8601 (ex: 2026-01-20T14:22:50-03:00)
    
    Returns:
        datetime: Objeto datetime ou None se conversão falhar
    """
    if not dt_string:
        return None
    try:
        # Remove timezone para simplificar
        dt_clean = dt_string.split('-03:00')[0].split('+')[0]
        return datetime.fromisoformat(dt_clean)
    except (ValueError, IndexError):
        return None


def get_status_description(cstat: str) -> str:
    """
    Retorna descrição do status da NFSe baseado no código.
    
    Args:
        cstat: Código de status (ex: "100")
    
    Returns:
        str: Descrição do status
    """
    status_map = {
        "100": "Ativa",
        "101": "Cancelada",
        "102": "Substituída",
    }
    return status_map.get(cstat, "Desconhecido")


def parse_nfse_xml(xml_path: str) -> Dict[str, Any]:
    """
    Processa um arquivo XML de NFSe e extrai todos os campos relevantes.
    
    Args:
        xml_path: Caminho para o arquivo XML
    
    Returns:
        Dict: Dicionário com todos os dados da NFSe estruturados
    
    Raises:
        FileNotFoundError: Se arquivo não existir
        ET.ParseError: Se XML estiver malformado
    """
    # Carregar e parsear XML
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Localizar elementos principais
    inf_nfse = root.find('.//nfse:infNFSe', NAMESPACE)
    
    # Extrair chave de acesso (atributo Id do infNFSe)
    chave_acesso = inf_nfse.get('Id', '') if inf_nfse is not None else ""
    # Remover prefixo "NFS" se presente (padrão do Portal Nacional)
    if chave_acesso.startswith('NFS'):
        chave_acesso = chave_acesso[3:]
    
    emit = inf_nfse.find('.//nfse:emit', NAMESPACE)
    valores_resumo = inf_nfse.find('.//nfse:valores', NAMESPACE)
    
    # DPS (Declaração de Prestação de Serviços)
    dps = inf_nfse.find('.//nfse:DPS', NAMESPACE)
    inf_dps = dps.find('.//nfse:infDPS', NAMESPACE) if dps is not None else None
    
    # Elementos dentro de infDPS
    prest = inf_dps.find('.//nfse:prest', NAMESPACE) if inf_dps is not None else None
    toma = inf_dps.find('.//nfse:toma', NAMESPACE) if inf_dps is not None else None
    serv = inf_dps.find('.//nfse:serv', NAMESPACE) if inf_dps is not None else None
    valores_det = inf_dps.find('.//nfse:valores', NAMESPACE) if inf_dps is not None else None
    trib = valores_det.find('.//nfse:trib', NAMESPACE) if valores_det is not None else None
    
    # ===========================================================================
    # IDENTIFICAÇÃO DA NOTA
    # ===========================================================================
    
    numero_nfse = safe_find_text(inf_nfse, './/nfse:nNFSe', NAMESPACE)
    numero_dfse = safe_find_text(inf_nfse, './/nfse:nDFSe', NAMESPACE)
    codigo_status = safe_find_text(inf_nfse, './/nfse:cStat', NAMESPACE)
    status = get_status_description(codigo_status)
    
    dh_proc_str = safe_find_text(inf_nfse, './/nfse:dhProc', NAMESPACE)
    dh_proc = parse_datetime(dh_proc_str)
    data_processamento = dh_proc.strftime("%d/%m/%Y %H:%M:%S") if dh_proc else dh_proc_str
    
    dh_emi_str = safe_find_text(inf_dps, './/nfse:dhEmi', NAMESPACE) if inf_dps else ""
    dh_emi = parse_datetime(dh_emi_str)
    data_emissao = dh_emi.strftime("%d/%m/%Y %H:%M:%S") if dh_emi else dh_emi_str
    
    d_compet_str = safe_find_text(inf_dps, './/nfse:dCompet', NAMESPACE) if inf_dps else ""
    try:
        d_compet = datetime.strptime(d_compet_str, "%Y-%m-%d") if d_compet_str else None
        data_competencia = d_compet.strftime("%d/%m/%Y") if d_compet else d_compet_str
    except ValueError:
        data_competencia = d_compet_str
    
    # ===========================================================================
    # EMITENTE
    # ===========================================================================
    
    emitente = {
        "cnpj": safe_find_text(emit, './/nfse:CNPJ', NAMESPACE),
        "inscricao_municipal": safe_find_text(emit, './/nfse:IM', NAMESPACE),
        "razao_social": safe_find_text(emit, './/nfse:xNome', NAMESPACE),
        "logradouro": safe_find_text(emit, './/nfse:enderNac/nfse:xLgr', NAMESPACE),
        "numero": safe_find_text(emit, './/nfse:enderNac/nfse:nro', NAMESPACE),
        "bairro": safe_find_text(emit, './/nfse:enderNac/nfse:xBairro', NAMESPACE),
        "codigo_municipio": safe_find_text(emit, './/nfse:enderNac/nfse:cMun', NAMESPACE),
        "uf": safe_find_text(emit, './/nfse:enderNac/nfse:UF', NAMESPACE),
        "cep": safe_find_text(emit, './/nfse:enderNac/nfse:CEP', NAMESPACE),
        "telefone": safe_find_text(emit, './/nfse:fone', NAMESPACE),
        "email": safe_find_text(emit, './/nfse:email', NAMESPACE),
    }
    
    # ===========================================================================
    # TOMADOR
    # ===========================================================================
    
    tomador_cnpj = safe_find_text(toma, './/nfse:CNPJ', NAMESPACE) if toma else ""
    tomador_cpf = safe_find_text(toma, './/nfse:CPF', NAMESPACE) if toma else ""
    tipo_pessoa = "PJ" if tomador_cnpj else "PF" if tomador_cpf else "N/A"
    documento_tomador = tomador_cnpj or tomador_cpf
    
    tomador = {
        "tipo_pessoa": tipo_pessoa,
        "cnpj_cpf": documento_tomador,
        "razao_social_nome": safe_find_text(toma, './/nfse:xNome', NAMESPACE) if toma else "",
        "codigo_municipio": safe_find_text(toma, './/nfse:end/nfse:endNac/nfse:cMun', NAMESPACE) if toma else "",
        "cep": safe_find_text(toma, './/nfse:end/nfse:endNac/nfse:CEP', NAMESPACE) if toma else "",
        "logradouro": safe_find_text(toma, './/nfse:end/nfse:xLgr', NAMESPACE) if toma else "",
        "numero": safe_find_text(toma, './/nfse:end/nfse:nro', NAMESPACE) if toma else "",
        "complemento": safe_find_text(toma, './/nfse:end/nfse:xCpl', NAMESPACE) if toma else "",
        "bairro": safe_find_text(toma, './/nfse:end/nfse:xBairro', NAMESPACE) if toma else "",
        "email": safe_find_text(toma, './/nfse:email', NAMESPACE) if toma else "",
    }
    
    # ===========================================================================
    # SERVIÇO
    # ===========================================================================
    
    servico = {
        "codigo_local_prestacao": safe_find_text(serv, './/nfse:locPrest/nfse:cLocPrestacao', NAMESPACE) if serv else "",
        "codigo_tributacao_nacional": safe_find_text(serv, './/nfse:cServ/nfse:cTribNac', NAMESPACE) if serv else "",
        "descricao_servico": safe_find_text(serv, './/nfse:cServ/nfse:xDescServ', NAMESPACE) if serv else "",
        "codigo_nbs": safe_find_text(serv, './/nfse:cServ/nfse:cNBS', NAMESPACE) if serv else "",
        "descricao_tributacao_nacional": safe_find_text(inf_nfse, './/nfse:xTribNac', NAMESPACE),
        "descricao_nbs": safe_find_text(inf_nfse, './/nfse:xNBS', NAMESPACE),
    }
    
    # ===========================================================================
    # VALORES RESUMIDOS
    # ===========================================================================
    
    valor_bc = safe_find_float(valores_resumo, './/nfse:vBC', NAMESPACE)
    aliquota_issqn = safe_find_float(valores_resumo, './/nfse:pAliqAplic', NAMESPACE)
    valor_issqn = safe_find_float(valores_resumo, './/nfse:vISSQN', NAMESPACE)
    valor_total_retido = safe_find_float(valores_resumo, './/nfse:vTotalRet', NAMESPACE)
    valor_liquido = safe_find_float(valores_resumo, './/nfse:vLiq', NAMESPACE)
    
    # ===========================================================================
    # TRIBUTOS DETALHADOS
    # ===========================================================================
    
    # Tributos Municipais
    trib_mun = trib.find('.//nfse:tribMun', NAMESPACE) if trib is not None else None
    tipo_ret_issqn = safe_find_text(trib_mun, './/nfse:tpRetISSQN', NAMESPACE) if trib_mun else ""
    # tpRetISSQN: 1 = NÃO retido (devido), 2 = Retido
    issqn_retido = tipo_ret_issqn == "2"
    
    # Tributos Federais - PIS/COFINS
    trib_fed = trib.find('.//nfse:tribFed', NAMESPACE) if trib is not None else None
    piscofins = trib_fed.find('.//nfse:piscofins', NAMESPACE) if trib_fed is not None else None
    
    cst_pis_cofins = safe_find_text(piscofins, './/nfse:CST', NAMESPACE) if piscofins else ""
    bc_pis_cofins = safe_find_float(piscofins, './/nfse:vBCPisCofins', NAMESPACE) if piscofins else 0.0
    aliq_pis = safe_find_float(piscofins, './/nfse:pAliqPis', NAMESPACE) if piscofins else 0.0
    aliq_cofins = safe_find_float(piscofins, './/nfse:pAliqCofins', NAMESPACE) if piscofins else 0.0
    valor_pis = safe_find_float(piscofins, './/nfse:vPis', NAMESPACE) if piscofins else 0.0
    valor_cofins = safe_find_float(piscofins, './/nfse:vCofins', NAMESPACE) if piscofins else 0.0
    tipo_ret_pis_cofins = safe_find_text(piscofins, './/nfse:tpRetPisCofins', NAMESPACE) if piscofins else ""
    # tpRetPisCofins: 1 = NÃO retido (devido), 2 = Retido
    pis_cofins_retido = tipo_ret_pis_cofins == "2"
    
    # Outros Tributos Federais
    valor_irrf = safe_find_float(trib_fed, './/nfse:vRetIRRF', NAMESPACE) if trib_fed else 0.0
    valor_csll = safe_find_float(trib_fed, './/nfse:vRetCSLL', NAMESPACE) if trib_fed else 0.0
    
    # Total de Tributos (%)
    tot_trib = trib.find('.//nfse:totTrib/nfse:pTotTrib', NAMESPACE) if trib is not None else None
    perc_trib_fed = safe_find_float(tot_trib, './/nfse:pTotTribFed', NAMESPACE) if tot_trib else 0.0
    perc_trib_est = safe_find_float(tot_trib, './/nfse:pTotTribEst', NAMESPACE) if tot_trib else 0.0
    perc_trib_mun = safe_find_float(tot_trib, './/nfse:pTotTribMun', NAMESPACE) if tot_trib else 0.0
    
    # ===========================================================================
    # LOCALIZAÇÃO
    # ===========================================================================
    
    localizacao = {
        "local_emissao": safe_find_text(inf_nfse, './/nfse:xLocEmi', NAMESPACE),
        "local_prestacao": safe_find_text(inf_nfse, './/nfse:xLocPrestacao', NAMESPACE),
        "codigo_municipio_incidencia": safe_find_text(inf_nfse, './/nfse:cLocIncid', NAMESPACE),
        "municipio_incidencia": safe_find_text(inf_nfse, './/nfse:xLocIncid', NAMESPACE),
    }
    
    # ===========================================================================
    # REGIME TRIBUTÁRIO
    # ===========================================================================
    
    reg_trib = prest.find('.//nfse:regTrib', NAMESPACE) if prest is not None else None
    regime = {
        "optante_simples_nacional": safe_find_text(reg_trib, './/nfse:opSimpNac', NAMESPACE) == "1" if reg_trib else False,
        "regime_especial_tributacao": safe_find_text(reg_trib, './/nfse:regEspTrib', NAMESPACE) if reg_trib else "",
    }
    
    # ===========================================================================
    # METADADOS
    # ===========================================================================
    
    metadados = {
        "versao_nfse": root.get("versao", ""),
        "versao_dps": dps.get("versao", "") if dps is not None else "",
        "versao_aplicativo": safe_find_text(inf_nfse, './/nfse:verAplic', NAMESPACE),
        "ambiente": "Produção" if safe_find_text(inf_dps, './/nfse:tpAmb', NAMESPACE) == "1" else "Homologação" if inf_dps else "N/A",
        "tipo_emissao": safe_find_text(inf_nfse, './/nfse:tpEmis', NAMESPACE),
        "processo_emissao": safe_find_text(inf_nfse, './/nfse:procEmi', NAMESPACE),
        "serie": safe_find_text(inf_dps, './/nfse:serie', NAMESPACE) if inf_dps else "",
        "numero_dps": safe_find_text(inf_dps, './/nfse:nDPS', NAMESPACE) if inf_dps else "",
    }
    
    # ===========================================================================
    # ESTRUTURA FINAL
    # ===========================================================================
    
    nfse_data = {
        # Identificação
        "chave_acesso": chave_acesso,
        "numero_nfse": numero_nfse,
        "numero_dfse": numero_dfse,
        "status": status,
        "codigo_status": codigo_status,
        "data_emissao": data_emissao,
        "data_processamento": data_processamento,
        "data_competencia": data_competencia,
        
        # Partes
        "emitente": emitente,
        "tomador": tomador,
        
        # Serviço
        "servico": servico,
        
        # Valores
        "valor_bruto": valor_bc,
        "valor_liquido": valor_liquido,
        "valor_total_retido": valor_total_retido,
        
        # Tributos
        "issqn": {
            "aliquota": aliquota_issqn,
            "valor": valor_issqn,
            "retido": issqn_retido,
        },
        "pis": {
            "cst": cst_pis_cofins,
            "base_calculo": bc_pis_cofins,
            "aliquota": aliq_pis,
            "valor": valor_pis,
            "retido": pis_cofins_retido,
        },
        "cofins": {
            "cst": cst_pis_cofins,
            "base_calculo": bc_pis_cofins,
            "aliquota": aliq_cofins,
            "valor": valor_cofins,
            "retido": pis_cofins_retido,
        },
        "irrf": {
            "valor": valor_irrf,
        },
        "csll": {
            "valor": valor_csll,
        },
        "percentual_tributos": {
            "federal": perc_trib_fed,
            "estadual": perc_trib_est,
            "municipal": perc_trib_mun,
        },
        
        # Localização
        "localizacao": localizacao,
        
        # Regime
        "regime": regime,
        
        # Metadados
        "metadados": metadados,
        
        # Arquivo original
        "arquivo_original": Path(xml_path).name,
    }
    
    return nfse_data


def parse_multiple_nfse(xml_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Processa múltiplos arquivos XML de NFSe.
    
    Args:
        xml_paths: Lista de caminhos para arquivos XML
    
    Returns:
        List[Dict]: Lista de dicionários com dados das NFSe
    """
    notas = []
    erros = []
    
    for xml_path in xml_paths:
        try:
            nota = parse_nfse_xml(xml_path)
            notas.append(nota)
        except Exception as e:
            erros.append({
                "arquivo": Path(xml_path).name,
                "erro": str(e)
            })
    
    # Se houver erros, adicionar ao resultado
    if erros:
        print(f"ATENÇÃO: {len(erros)} arquivo(s) com erro:")
        for erro in erros:
            print(f"  - {erro['arquivo']}: {erro['erro']}")
    
    return notas


def format_currency(value: float) -> str:
    """
    Formata valor monetário no padrão brasileiro.
    
    Args:
        value: Valor numérico
    
    Returns:
        str: Valor formatado (ex: "R$ 1.234,56")
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float) -> str:
    """
    Formata percentual.
    
    Args:
        value: Valor percentual
    
    Returns:
        str: Percentual formatado (ex: "5,00%")
    """
    return f"{value:.2f}%".replace(".", ",")


# ==============================================================================
# TESTES
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python parser_nfse.py <arquivo.xml>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    try:
        nota = parse_nfse_xml(xml_file)
        
        print("="*70)
        print("DADOS DA NFSe EXTRAÍDOS")
        print("="*70)
        print(f"\nNúmero: {nota['numero_nfse']}")
        print(f"Status: {nota['status']}")
        print(f"Data Emissão: {nota['data_emissao']}")
        print(f"\nEmitente: {nota['emitente']['razao_social']}")
        print(f"CNPJ: {nota['emitente']['cnpj']}")
        print(f"\nTomador: {nota['tomador']['razao_social_nome']}")
        print(f"CNPJ/CPF: {nota['tomador']['cnpj_cpf']}")
        print(f"\nValor Bruto: {format_currency(nota['valor_bruto'])}")
        print(f"Valor Líquido: {format_currency(nota['valor_liquido'])}")
        print(f"Total Retido: {format_currency(nota['valor_total_retido'])}")
        print(f"\nPIS: {format_currency(nota['pis']['valor'])}")
        print(f"COFINS: {format_currency(nota['cofins']['valor'])}")
        print(f"IRRF: {format_currency(nota['irrf']['valor'])}")
        print(f"CSLL: {format_currency(nota['csll']['valor'])}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"Erro ao processar XML: {e}")
        sys.exit(1)
