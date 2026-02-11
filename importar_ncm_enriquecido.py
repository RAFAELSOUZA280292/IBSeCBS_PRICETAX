"""
Script para importar descrições enriquecidas pelo ChatGPT de volta para a planilha TIPI.
"""

import pandas as pd
from pathlib import Path

def importar_descricoes_enriquecidas(arquivo_enriquecido: str = "ncm_enriquecido.csv"):
    """
    Importa descrições enriquecidas e atualiza a planilha TIPI.
    
    Args:
        arquivo_enriquecido: Caminho para o CSV retornado pelo ChatGPT
    """
    print("=" * 80)
    print("IMPORTAÇÃO DE DESCRIÇÕES ENRIQUECIDAS")
    print("=" * 80)
    
    # 1. Carregar planilha original
    print("\n1. Carregando planilha original...")
    df_original = pd.read_excel("PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx")
    print(f"    {len(df_original)} NCMs carregados")
    
    # 2. Carregar descrições enriquecidas
    print("\n2. Carregando descrições enriquecidas...")
    if not Path(arquivo_enriquecido).exists():
        print(f"    ERRO: Arquivo '{arquivo_enriquecido}' não encontrado!")
        print(f"   → Certifique-se de que o ChatGPT retornou o arquivo e você o salvou neste diretório.")
        return False
    
    df_enriquecido = pd.read_csv(arquivo_enriquecido)
    print(f"    {len(df_enriquecido)} descrições enriquecidas carregadas")
    
    # 3. Validar estrutura
    print("\n3. Validando estrutura do arquivo...")
    colunas_esperadas = ["NCM", "NCM_DESCRICAO_ORIGINAL", "NCM_DESCRICAO_ENRIQUECIDA"]
    colunas_presentes = df_enriquecido.columns.tolist()
    
    if not all(col in colunas_presentes for col in colunas_esperadas):
        print(f"    ERRO: Estrutura inválida!")
        print(f"   Esperado: {colunas_esperadas}")
        print(f"   Encontrado: {colunas_presentes}")
        return False
    
    print(f"    Estrutura válida")
    
    # 4. Criar backup
    print("\n4. Criando backup da planilha original...")
    backup_path = "PLANILHA_PRICETAX_REGRAS_REFINADAS_BACKUP_PRE_ENRIQUECIMENTO.xlsx"
    df_original.to_excel(backup_path, index=False)
    print(f"    Backup salvo: {backup_path}")
    
    # 5. Mesclar descrições enriquecidas
    print("\n5. Mesclando descrições enriquecidas...")
    
    # Converter NCM para string em ambos os DataFrames
    df_original["NCM"] = df_original["NCM"].astype(str)
    df_enriquecido["NCM"] = df_enriquecido["NCM"].astype(str)
    
    # Criar dicionário de mapeamento NCM -> Descrição Enriquecida
    mapa_enriquecido = dict(zip(
        df_enriquecido["NCM"],
        df_enriquecido["NCM_DESCRICAO_ENRIQUECIDA"]
    ))
    
    # Atualizar descrições
    alteracoes = 0
    for idx, row in df_original.iterrows():
        ncm = str(row["NCM"])
        if ncm in mapa_enriquecido:
            desc_nova = mapa_enriquecido[ncm]
            desc_antiga = row["NCM_DESCRICAO"]
            
            # Só atualizar se for diferente
            if desc_nova != desc_antiga:
                df_original.at[idx, "NCM_DESCRICAO"] = desc_nova
                alteracoes += 1
    
    print(f"    {alteracoes} descrições atualizadas")
    print(f"    {len(df_original) - alteracoes} descrições mantidas")
    
    # 6. Salvar planilha atualizada
    print("\n6. Salvando planilha atualizada...")
    df_original.to_excel("PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx", index=False)
    print(f"    Planilha salva: PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx")
    
    # 7. Relatório de alterações
    print("\n" + "=" * 80)
    print("RELATÓRIO DE ALTERAÇÕES")
    print("=" * 80)
    print(f"Total de NCMs: {len(df_original)}")
    print(f"Descrições alteradas: {alteracoes}")
    print(f"Descrições mantidas: {len(df_original) - alteracoes}")
    print(f"Taxa de alteração: {alteracoes / len(df_original) * 100:.1f}%")
    
    # Mostrar exemplos de alterações
    print("\n EXEMPLOS DE ALTERAÇÕES:")
    exemplos = df_enriquecido[
        df_enriquecido["NCM_DESCRICAO_ORIGINAL"] != df_enriquecido["NCM_DESCRICAO_ENRIQUECIDA"]
    ].head(10)
    
    for idx, row in exemplos.iterrows():
        print(f"\nNCM: {row['NCM']}")
        print(f"  ANTES: {row['NCM_DESCRICAO_ORIGINAL']}")
        print(f"  DEPOIS: {row['NCM_DESCRICAO_ENRIQUECIDA']}")
    
    print("\n" + "=" * 80)
    print("IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print(f"\n Backup disponível em: {backup_path}")
    print(f" Planilha atualizada: PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx")
    print(f"\n Próximo passo: Fazer commit e push para o GitHub")
    
    return True

if __name__ == "__main__":
    import sys
    
    arquivo = "ncm_enriquecido.csv"
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
    
    sucesso = importar_descricoes_enriquecidas(arquivo)
    
    if not sucesso:
        sys.exit(1)
