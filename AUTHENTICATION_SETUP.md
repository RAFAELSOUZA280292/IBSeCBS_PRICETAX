# Configuração de Autenticação no Streamlit Cloud

## Visão Geral

O PRICETAX agora possui autenticação obrigatória para proteger dados sensíveis. Este documento explica como configurar as credenciais no Streamlit Cloud.

---

## Credenciais Configuradas

**Usuário:** `PriceADM`  
**Senha:** `Ivana2026`

---

## Configuração no Streamlit Cloud

### Passo 1: Acessar Configurações

1. Acesse https://share.streamlit.io
2. Faça login com sua conta
3. Localize o app **IBSeCBS_PRICETAX**
4. Clique em **"Manage app"** (canto inferior direito)

### Passo 2: Configurar Secrets

1. No menu lateral, clique em **"Secrets"**
2. Cole o seguinte conteúdo:

```toml
[passwords]
PriceADM = "84806ce7d5562fa27310c62dc674e8f248da4a34a28f8392feb9ec08c6615f04"
```

3. Clique em **"Save"**
4. O app será reiniciado automaticamente

### Passo 3: Testar Autenticação

1. Acesse https://ibsecbs-pricetax.streamlit.app
2. Você verá a tela de login
3. Digite:
   - **Usuário:** `PriceADM`
   - **Senha:** `Ivana2026`
4. Clique em **"Entrar"**
5. Se as credenciais estiverem corretas, você será autenticado

---

## Segurança

### Como funciona

1. **Hash SHA-256:** A senha é armazenada como hash, não em texto plano
2. **Secrets criptografados:** O Streamlit Cloud criptografa o arquivo `secrets.toml`
3. **Session state:** Login persiste durante a sessão do navegador
4. **Logout:** Botão "Sair" no sidebar limpa a sessão

### Adicionar novos usuários

Para adicionar um novo usuário:

1. Gere o hash SHA-256 da senha:

```python
import hashlib
senha = "SuaSenhaAqui"
hash_senha = hashlib.sha256(senha.encode()).hexdigest()
print(hash_senha)
```

2. Adicione no `secrets.toml`:

```toml
[passwords]
PriceADM = "84806ce7d5562fa27310c62dc674e8f248da4a34a28f8392feb9ec08c6615f04"
NovoUsuario = "hash_gerado_aqui"
```

3. Salve e o app reiniciará

---

## Arquivos Modificados

### Novos arquivos

- `auth.py` - Módulo de autenticação
- `.streamlit/secrets.toml` - Credenciais (NÃO commitado no Git)
- `AUTHENTICATION_SETUP.md` - Esta documentação

### Arquivos modificados

- `app.py` - Adicionada verificação de autenticação
- `.gitignore` - Adicionado `.streamlit/secrets.toml`

---

## Troubleshooting

### Erro: "Erro de configuração: credenciais não encontradas"

**Causa:** O arquivo `secrets.toml` não foi configurado no Streamlit Cloud.

**Solução:** Siga o Passo 2 acima para configurar os secrets.

### Erro: "Usuário ou senha incorretos"

**Causa:** Credenciais digitadas incorretamente.

**Solução:** Verifique se está usando:
- Usuário: `PriceADM` (case-sensitive)
- Senha: `Ivana2026` (case-sensitive)

### Não consigo fazer logout

**Solução:** Clique no botão "Sair" no sidebar ou limpe os cookies do navegador.

---

## Contato

Para suporte ou dúvidas sobre autenticação, entre em contato com o administrador do sistema.
