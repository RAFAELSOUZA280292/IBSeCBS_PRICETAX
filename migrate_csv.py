"""
Script de Migração de CSV - Adicionar Campos IPI
=================================================

Migra arquivo xml_nfe_data.csv de 32 campos para 36 campos (adiciona IPI).

Autor: PRICETAX Intelligence System
Data: 2026-01-29
"""

import pandas as pd
import os
import shutil
from datetime import datetime


def migrate_csv():
    """
    Migra CSV antigo (32 campos) para novo formato (36 campos com IPI).
    """
    
    data_file = "logs/xml_nfe_data.csv"
    
    if not os.path.isfile(data_file):
        print("Arquivo não encontrado. Nada a migrar.")
        return
    
    # Fazer backup
    backup_file = f"logs/xml_nfe_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    shutil.copy(data_file, backup_file)
    print(f"Backup criado: {backup_file}")
    
    try:
        # Ler CSV antigo
        df = pd.read_csv(data_file)
        
        # Verificar se já tem os campos IPI
        if 'cst_ipi' in df.columns:
            print("CSV já está no formato novo. Nada a migrar.")
            return
        
        # Adicionar campos IPI após vcofins
        campos_ipi = ['cst_ipi', 'vbc_ipi', 'pipi', 'vipi']
        
        # Encontrar posição de vcofins
        colunas = df.columns.tolist()
        idx_vcofins = colunas.index('vcofins')
        
        # Inserir campos IPI após vcofins
        for i, campo in enumerate(campos_ipi):
            df.insert(idx_vcofins + 1 + i, campo, '')
            
            # Preencher com valores padrão
            if campo in ['vbc_ipi', 'pipi', 'vipi']:
                df[campo] = 0.0
            else:
                df[campo] = ''
        
        # Salvar CSV migrado
        df.to_csv(data_file, index=False, encoding='utf-8')
        print(f"CSV migrado com sucesso: {len(df)} registros")
        print(f"Campos adicionados: {', '.join(campos_ipi)}")
        print(f"Total de colunas: {len(df.columns)}")
        
    except Exception as e:
        print(f"Erro na migração: {e}")
        print(f"Restaurando backup...")
        shutil.copy(backup_file, data_file)
        print("Backup restaurado.")


if __name__ == "__main__":
    migrate_csv()
