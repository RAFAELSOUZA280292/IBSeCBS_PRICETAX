import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import re
from logger_config import get_logger

# Configurar logging
logger = get_logger(__name__)

def parse_nfe_xml(xml_path: str) -> Dict[str, Any]:
    """
    Extrai dados estruturados de um XML de NF-e (incluindo IBS/CBS da Reforma Tributária).
    
    Args:
        xml_path: Caminho para o arquivo XML
    
    Retorna:
        dict com:
        - emitente: {cnpj, razao_social, uf}
        - itens: lista com dados completos incluindo IBS/CBS
        - erro: str (se houver erro no processamento)
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"XML corrompido ou inválido ({xml_path}): {e}")
        return {
            'erro': 'XML_INVALIDO',
            'detalhes': f"Erro ao fazer parse do XML: {str(e)}",
            'emitente': {},
            'destinatario': {},
            'itens': []
        }
    except FileNotFoundError:
        logger.error(f"Arquivo XML não encontrado: {xml_path}")
        return {
            'erro': 'ARQUIVO_NAO_ENCONTRADO',
            'detalhes': f"Arquivo não encontrado: {xml_path}",
            'emitente': {},
            'destinatario': {},
            'itens': []
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao processar XML ({xml_path}): {e}")
        return {
            'erro': 'ERRO_INESPERADO',
            'detalhes': str(e),
            'emitente': {},
            'destinatario': {},
            'itens': []
        }
    
    # Namespace padrão NFe
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Extrair dados do emitente
    emit = root.find('.//nfe:emit', ns)
    
    emitente = {}
    if emit is not None:
        cnpj_elem = emit.find('nfe:CNPJ', ns)
        razao_elem = emit.find('nfe:xNome', ns)
        uf_elem = emit.find('nfe:enderEmit/nfe:UF', ns)
        
        emitente = {
            'cnpj': cnpj_elem.text if cnpj_elem is not None else '',
            'razao_social': razao_elem.text if razao_elem is not None else '',
            'uf': uf_elem.text if uf_elem is not None else ''
        }
    
    # Extrair dados do destinatário
    dest = root.find('.//nfe:dest', ns)
    
    destinatario = {}
    if dest is not None:
        cnpj_dest_elem = dest.find('nfe:CNPJ', ns)
        cpf_dest_elem = dest.find('nfe:CPF', ns)
        razao_dest_elem = dest.find('nfe:xNome', ns)
        uf_dest_elem = dest.find('nfe:enderDest/nfe:UF', ns)
        
        destinatario = {
            'cnpj': cnpj_dest_elem.text if cnpj_dest_elem is not None else (cpf_dest_elem.text if cpf_dest_elem is not None else ''),
            'razao_social': razao_dest_elem.text if razao_dest_elem is not None else '',
            'uf': uf_dest_elem.text if uf_dest_elem is not None else ''
        }
    
    # Extrair data de emissão
    ide = root.find('.//nfe:ide', ns)
    data_emissao = ''
    if ide is not None:
        dhemi_elem = ide.find('nfe:dhEmi', ns)
        if dhemi_elem is not None:
            data_emissao = dhemi_elem.text    
    # Extrair itens
    itens = []
    det_list = root.findall('.//nfe:det', ns)
    if not det_list:
        det_list = root.findall('.//det')  # Tentar sem namespace
    
    for det in det_list:
        prod = det.find('nfe:prod', ns)
        imposto = det.find('nfe:imposto', ns)
        
        if prod is not None:
            # Dados do produto
            ncm_elem = prod.find('nfe:NCM', ns)
            cfop_elem = prod.find('nfe:CFOP', ns)
            desc_elem = prod.find('nfe:xProd', ns)
            vuncom_elem = prod.find('nfe:vUnCom', ns)
            qcom_elem = prod.find('nfe:qCom', ns)
            vprod_elem = prod.find('nfe:vProd', ns)
            
            # Sanitizar descrição (remover prefixos técnicos como "arrItem_1right")
            descricao_raw = desc_elem.text if desc_elem is not None else ''
            # Regex: ^arrItem_\d+[a-z]*\s* captura "arrItem_" + dígitos + letras minúsculas opcionais + espaços
            descricao_limpa = re.sub(r'^arrItem_\d+[a-z]*\s*', '', descricao_raw).strip()
            
            item = {
                'ncm': ncm_elem.text if ncm_elem is not None else '',
                'cfop': cfop_elem.text if cfop_elem is not None else '',
                'descricao': descricao_limpa,
                'valor_unitario': float(vuncom_elem.text) if vuncom_elem is not None else 0.0,
                'quantidade': float(qcom_elem.text) if qcom_elem is not None else 0.0,
                'valor_total': float(vprod_elem.text) if vprod_elem is not None else 0.0,
                'cst_icms': '',
                'cst_pis': '',
                'cst_cofins': '',
                'vbc_icms': 0.0,
                'vicms': 0.0,
                'vbc_pis': 0.0,
                'vpis': 0.0,
                'vbc_cofins': 0.0,
                'vcofins': 0.0,
                # IPI
                'cst_ipi': '',
                'vbc_ipi': 0.0,
                'pipi': 0.0,
                'vipi': 0.0,
                # Campos IBS/CBS (Reforma Tributária)
                'cst_ibscbs': '',
                'cclasstrib': '',
                'vibs': 0.0,
                'vcbs': 0.0,
                'vbc_ibscbs': 0.0,
                'pibs': 0.0,
                'pcbs': 0.0
            }
            
            # Extrair CST e valores de impostos
            if imposto is not None:
                # ICMS
                icms = imposto.find('nfe:ICMS', ns)
                if icms is not None:
                    # Pode ser ICMS00, ICMS10, ICMS20, etc.
                    for child in icms:
                        cst_elem = child.find('nfe:CST', ns)
                        if cst_elem is None:
                            cst_elem = child.find('nfe:CSOSN', ns)
                        vbc_elem = child.find('nfe:vBC', ns)
                        vicms_elem = child.find('nfe:vICMS', ns)
                        
                        if cst_elem is not None:
                            item['cst_icms'] = cst_elem.text
                        if vbc_elem is not None:
                            item['vbc_icms'] = float(vbc_elem.text)
                        if vicms_elem is not None:
                            item['vicms'] = float(vicms_elem.text)
                
                # PIS
                pis = imposto.find('nfe:PIS', ns)
                if pis is not None:
                    for child in pis:
                        cst_elem = child.find('nfe:CST', ns)
                        vbc_elem = child.find('nfe:vBC', ns)
                        vpis_elem = child.find('nfe:vPIS', ns)
                        
                        if cst_elem is not None:
                            item['cst_pis'] = cst_elem.text
                        if vbc_elem is not None:
                            item['vbc_pis'] = float(vbc_elem.text)
                        if vpis_elem is not None:
                            item['vpis'] = float(vpis_elem.text)
                
                # COFINS
                cofins = imposto.find('nfe:COFINS', ns)
                if cofins is not None:
                    for child in cofins:
                        cst_elem = child.find('nfe:CST', ns)
                        vbc_elem = child.find('nfe:vBC', ns)
                        vcofins_elem = child.find('nfe:vCOFINS', ns)
                        
                        if cst_elem is not None:
                            item['cst_cofins'] = cst_elem.text
                        if vbc_elem is not None:
                            item['vbc_cofins'] = float(vbc_elem.text)
                        if vcofins_elem is not None:
                            item['vcofins'] = float(vcofins_elem.text)
                
                # IPI
                ipi = imposto.find('nfe:IPI', ns)
                if ipi is not None:
                    # IPI pode ter IPITrib ou IPINT
                    ipi_trib = ipi.find('nfe:IPITrib', ns)
                    if ipi_trib is not None:
                        cst_elem = ipi_trib.find('nfe:CST', ns)
                        vbc_elem = ipi_trib.find('nfe:vBC', ns)
                        pipi_elem = ipi_trib.find('nfe:pIPI', ns)
                        vipi_elem = ipi_trib.find('nfe:vIPI', ns)
                        
                        if cst_elem is not None:
                            item['cst_ipi'] = cst_elem.text
                        if vbc_elem is not None:
                            item['vbc_ipi'] = float(vbc_elem.text)
                        if pipi_elem is not None:
                            item['pipi'] = float(pipi_elem.text)
                        if vipi_elem is not None:
                            item['vipi'] = float(vipi_elem.text)
                    else:
                        # IPINT (não tributado)
                        ipi_nt = ipi.find('nfe:IPINT', ns)
                        if ipi_nt is not None:
                            cst_elem = ipi_nt.find('nfe:CST', ns)
                            if cst_elem is not None:
                                item['cst_ipi'] = cst_elem.text
                
                # IBSCBS (Grupo IBS/CBS - Reforma Tributária 2026)
                ibscbs = imposto.find('nfe:IBSCBS', ns)
                if ibscbs is not None:
                    # CST e cClassTrib ficam no nível do IBSCBS
                    cst_elem = ibscbs.find('nfe:CST', ns)
                    cclasstrib_elem = ibscbs.find('nfe:cClassTrib', ns)
                    
                    if cst_elem is not None:
                        item['cst_ibscbs'] = cst_elem.text
                    if cclasstrib_elem is not None:
                        item['cclasstrib'] = cclasstrib_elem.text
                    
                    # Grupo gIBSCBS contém os valores
                    gibscbs = ibscbs.find('nfe:gIBSCBS', ns)
                    if gibscbs is not None:
                        # Base de cálculo
                        vbc_elem = gibscbs.find('nfe:vBC', ns)
                        if vbc_elem is not None:
                            item['vbc_ibscbs'] = float(vbc_elem.text)
                        
                        # IBS UF
                        gibsuf = gibscbs.find('nfe:gIBSUF', ns)
                        if gibsuf is not None:
                            pibsuf_elem = gibsuf.find('nfe:pIBSUF', ns)
                            vibsuf_elem = gibsuf.find('nfe:vIBSUF', ns)
                            if pibsuf_elem is not None:
                                item['pibs'] = float(pibsuf_elem.text)
                            if vibsuf_elem is not None:
                                item['vibs'] += float(vibsuf_elem.text)
                        
                        # IBS Município
                        gibsmun = gibscbs.find('nfe:gIBSMun', ns)
                        if gibsmun is not None:
                            vibsmun_elem = gibsmun.find('nfe:vIBSMun', ns)
                            if vibsmun_elem is not None:
                                item['vibs'] += float(vibsmun_elem.text)
                        
                        # CBS
                        gcbs = gibscbs.find('nfe:gCBS', ns)
                        if gcbs is not None:
                            pcbs_elem = gcbs.find('nfe:pCBS', ns)
                            vcbs_elem = gcbs.find('nfe:vCBS', ns)
                            if pcbs_elem is not None:
                                item['pcbs'] = float(pcbs_elem.text)
                            if vcbs_elem is not None:
                                item['vcbs'] = float(vcbs_elem.text)
            
            itens.append(item)
    
    return {
        'emitente': emitente,
        'destinatario': destinatario,
        'data_emissao': data_emissao,
        'itens': itens
    }

if __name__ == "__main__":
    # Teste
    import sys
    if len(sys.argv) > 1:
        resultado = parse_nfe_xml(sys.argv[1])
        print(f"Emitente: {resultado['emitente']}")
        print(f"Total de itens: {len(resultado['itens'])}")
        for i, item in enumerate(resultado['itens'][:3], 1):
            print(f"\nItem {i}:")
            print(f"  NCM: {item['ncm']}")
            print(f"  CFOP: {item['cfop']}")
            print(f"  Descrição: {item['descricao'][:50]}")
            print(f"  Valor Total: R$ {item['valor_total']:.2f}")
            print(f"  cClassTrib: {item['cclasstrib']}")
            print(f"  IBS: R$ {item['vibs']:.2f} ({item['pibs']:.4f}%)")
            print(f"  CBS: R$ {item['vcbs']:.2f} ({item['pcbs']:.4f}%)")
