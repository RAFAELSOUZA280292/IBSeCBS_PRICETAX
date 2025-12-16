import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import re

def parse_nfe_xml(xml_path: str) -> Dict[str, Any]:
    """
    Extrai dados estruturados de um XML de NF-e.
    
    Retorna:
        dict com:
        - emitente: {cnpj, razao_social, uf}
        - itens: lista de {ncm, cfop, descricao, valor_unitario, quantidade, valor_total, cst_icms, cst_pis, cst_cofins}
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Namespace padrão NFe
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Extrair dados do emitente
    emit = root.find('.//nfe:emit', ns)
    if emit is None:
        emit = root.find('.//emit')  # Tentar sem namespace
    
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
            
            item = {
                'ncm': ncm_elem.text if ncm_elem is not None else '',
                'cfop': cfop_elem.text if cfop_elem is not None else '',
                'descricao': desc_elem.text if desc_elem is not None else '',
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
                'vcofins': 0.0
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
            
            itens.append(item)
    
    return {
        'emitente': emitente,
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
            print(f"  Valor Unit: R$ {item['valor_unitario']:.2f}")
            print(f"  CST ICMS: {item['cst_icms']}")
