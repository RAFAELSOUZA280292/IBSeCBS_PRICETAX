"""
PRICETAX - Configuração de Logging
===================================

Módulo centralizado para configuração de logging estruturado.
Todos os módulos devem importar o logger deste arquivo.

Autor: PRICETAX
Data: 08/02/2026
"""

import logging
import sys
from pathlib import Path

# Diretório para logs
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Arquivo de log
LOG_FILE = LOG_DIR / "pricetax.log"

# Formato de log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        # Handler para arquivo (rotativo)
        logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        # Handler para console (apenas WARNING e acima)
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurar nível de log do console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Obter logger raiz
root_logger = logging.getLogger()

# Adicionar handler de console se não existir
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo.
    
    Args:
        name: Nome do módulo (geralmente __name__)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


# Logger padrão para importação direta
logger = get_logger('pricetax')
