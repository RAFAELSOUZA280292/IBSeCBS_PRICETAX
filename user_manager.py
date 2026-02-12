"""
Módulo de Gerenciamento de Usuários - PRICETAX

Gerencia status de usuários, controle de mensalidades e permissões de acesso.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Optional, List, Tuple


# Caminho do arquivo de status de usuários
USERS_STATUS_FILE = "usuarios_status.json"


def carregar_usuarios_status() -> Dict:
    """
    Carrega o arquivo de status de usuários.
    
    Returns:
        Dicionário com status de todos os usuários
    """
    if not os.path.exists(USERS_STATUS_FILE):
        return {}
    
    try:
        with open(USERS_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar status de usuários: {e}")
        return {}


def salvar_usuarios_status(usuarios: Dict) -> bool:
    """
    Salva o arquivo de status de usuários.
    
    Args:
        usuarios: Dicionário com status de todos os usuários
        
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        with open(USERS_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar status de usuários: {e}")
        return False


def verificar_acesso_usuario(username: str) -> Tuple[bool, Optional[str]]:
    """
    Verifica se o usuário tem acesso ao sistema.
    
    Args:
        username: Nome de usuário
        
    Returns:
        Tupla (pode_acessar, mensagem_erro)
        - pode_acessar: True se pode acessar, False se bloqueado
        - mensagem_erro: Mensagem de erro se bloqueado, None se pode acessar
    """
    usuarios = carregar_usuarios_status()
    
    # Se usuário não está no arquivo, permitir acesso (retrocompatibilidade)
    if username not in usuarios:
        return True, None
    
    user_data = usuarios[username]
    status = user_data.get("status", "ativo")
    
    # Verificar status
    if status == "bloqueado":
        return False, "Acesso bloqueado. Entre em contato com o administrador."
    
    if status == "inadimplente":
        return False, "Mensalidade em atraso. Entre em contato com nosso financeiro: financeiro@pricetax.com.br"
    
    # Verificar vencimento (se houver)
    data_vencimento_str = user_data.get("data_vencimento")
    if data_vencimento_str:
        try:
            data_vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
            hoje = date.today()
            
            if hoje > data_vencimento:
                # Atualizar status para inadimplente automaticamente
                usuarios[username]["status"] = "inadimplente"
                salvar_usuarios_status(usuarios)
                return False, "Mensalidade em atraso. Entre em contato com nosso financeiro: financeiro@pricetax.com.br"
        except Exception as e:
            print(f"Erro ao verificar vencimento: {e}")
    
    return True, None


def obter_info_usuario(username: str) -> Optional[Dict]:
    """
    Obtém informações de um usuário.
    
    Args:
        username: Nome de usuário
        
    Returns:
        Dicionário com informações do usuário ou None se não encontrado
    """
    usuarios = carregar_usuarios_status()
    return usuarios.get(username)


def atualizar_usuario(username: str, dados: Dict) -> bool:
    """
    Atualiza dados de um usuário.
    
    Args:
        username: Nome de usuário
        dados: Dicionário com dados a atualizar
        
    Returns:
        True se atualizou com sucesso, False caso contrário
    """
    usuarios = carregar_usuarios_status()
    
    if username not in usuarios:
        usuarios[username] = {}
    
    usuarios[username].update(dados)
    return salvar_usuarios_status(usuarios)


def adicionar_usuario(username: str, tipo: str = "cliente", data_vencimento: Optional[str] = None, observacoes: str = "") -> bool:
    """
    Adiciona um novo usuário ao sistema.
    
    Args:
        username: Nome de usuário
        tipo: Tipo de usuário (administrador, equipe, cliente)
        data_vencimento: Data de vencimento no formato YYYY-MM-DD
        observacoes: Observações sobre o usuário
        
    Returns:
        True se adicionou com sucesso, False caso contrário
    """
    usuarios = carregar_usuarios_status()
    
    if username in usuarios:
        return False  # Usuário já existe
    
    usuarios[username] = {
        "status": "ativo",
        "tipo": tipo,
        "data_cadastro": date.today().strftime("%Y-%m-%d"),
        "data_vencimento": data_vencimento,
        "observacoes": observacoes
    }
    
    return salvar_usuarios_status(usuarios)


def remover_usuario(username: str) -> bool:
    """
    Remove um usuário do sistema.
    
    Args:
        username: Nome de usuário
        
    Returns:
        True se removeu com sucesso, False caso contrário
    """
    usuarios = carregar_usuarios_status()
    
    if username not in usuarios:
        return False
    
    del usuarios[username]
    return salvar_usuarios_status(usuarios)


def listar_usuarios() -> List[Dict]:
    """
    Lista todos os usuários do sistema.
    
    Returns:
        Lista de dicionários com informações dos usuários
    """
    usuarios = carregar_usuarios_status()
    
    lista = []
    for username, dados in usuarios.items():
        user_info = {
            "username": username,
            **dados
        }
        lista.append(user_info)
    
    return lista


def contar_usuarios_por_status() -> Dict[str, int]:
    """
    Conta usuários por status.
    
    Returns:
        Dicionário com contagem por status
    """
    usuarios = carregar_usuarios_status()
    
    contagem = {
        "ativo": 0,
        "bloqueado": 0,
        "inadimplente": 0
    }
    
    for dados in usuarios.values():
        status = dados.get("status", "ativo")
        if status in contagem:
            contagem[status] += 1
    
    return contagem


def verificar_vencimentos_proximos(dias: int = 7) -> List[Dict]:
    """
    Verifica usuários com vencimento próximo.
    
    Args:
        dias: Número de dias para considerar "próximo"
        
    Returns:
        Lista de usuários com vencimento nos próximos X dias
    """
    usuarios = carregar_usuarios_status()
    hoje = date.today()
    
    vencimentos_proximos = []
    
    for username, dados in usuarios.items():
        data_vencimento_str = dados.get("data_vencimento")
        if not data_vencimento_str:
            continue
        
        try:
            data_vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
            dias_restantes = (data_vencimento - hoje).days
            
            if 0 <= dias_restantes <= dias:
                vencimentos_proximos.append({
                    "username": username,
                    "dias_restantes": dias_restantes,
                    "data_vencimento": data_vencimento_str,
                    **dados
                })
        except Exception as e:
            print(f"Erro ao verificar vencimento de {username}: {e}")
    
    return sorted(vencimentos_proximos, key=lambda x: x["dias_restantes"])
