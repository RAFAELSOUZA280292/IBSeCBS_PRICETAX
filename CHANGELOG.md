_#_ _Changelog_ - _Histórico_ _de_ _Alterações_ _do_ _Projeto_

**Autor:** _Manus_ _AI_
**Data:** _21_ _de_ _Janeiro_ _de_ _2026_

_---

_##_ _v4.2_ - _Correção_ _Estrutural_ _UnboundLocalError_ _(Janeiro_ _2026)_

### 🐛 Bug Fixes

-   **_Correção_ _de_ _UnboundLocalError_ _em_ _guess_cclasstrib_**
    -   _Removido_ _import_ _redundante_ _de_ `re` _dentro_ _da_ _função_ `guess_cclasstrib()` _(linha_ _802)._
    -   _Causa_ _raiz:_ _Python_ _marca_ `re` _como_ _variável_ _local_ _ao_ _ver_ _import_ _statement,_ _invalidando_ _o_ `re` _global._
    -   _Impacto:_ _Corrige_ _erro_ _ao_ _consultar_ _NCM_ _com_ _formatação_ _(ex:_ _8701.93.00)_ _e_ _CFOP._
    -   _Testado_ _com_ _16_ _casos_ _extremos:_ _100%_ _de_ _sucesso._

### 📝 Documentação

-   **_Análise_ _Profunda_ _do_ _Bug_**
    -   _Criado_ `bug_fix_documentation.md` _com_ _análise_ _completa_ _da_ _causa_ _raiz._
    -   _Documentadas_ _regras_ _de_ _escopo_ _do_ _Python_ _(LEGB)_ _e_ _prevenção_ _de_ _erros_ _similares._
    -   _Suite_ _de_ _testes_ _criada_ _(test_ncm_validation.py)_ _para_ _validação_ _contínua._

_---

_##_ _v4.1_ - _Refatoração_ _e_ _Correções_ _Críticas_ _(Janeiro_ _2026)_

### ✨ Features

-   **_Consulta_ _de_ _CNPJ_**
    -   _Adicionada_ _nova_ _aba_ _"Consulta_ _CNPJ"_ _para_ _busca_ _de_ _dados_ _cadastrais._
    -   _Integração_ _com_ _a_ _BrasilAPI_ _para_ _obter_ _dados_ _de_ _QSA,_ _regime_ _tributário_ _e_ _endereço._
    -   _Interface_ _profissional_ _com_ _padrão_ _de_ _cores_ _PRICETAX_ _(#FFDD00)._
    -   _Funcionalidade_ _de_ _exportação_ _para_ _CSV._

-   **_Refatoração_ _Completa_ _do_ _Mapeamento_ _cClassTrib_**
    -   _Criado_ _módulo_ `cclasstrib_mapping.py` _como_ _fonte_ _única_ _da_ _verdade._
    -   _Mapeamento_ _de_ **_TODOS_ _os_ _15_ _anexos_** _da_ _LC_ _214/2025_ _baseado_ _no_ _arquivo_ _oficial_ `classificacao_tributaria.xlsx`_.
    -   _Lógica_ _condicional_ _(if/elif)_ _removida_ _e_ _substituída_ _por_ _dicionário_ _de_ _mapeamento_ _robusto._

-   **_Seletor_ _de_ _Benefícios_ _Fiscais_**
    -   _Adicionado_ _seletor_ _(radio_ _button)_ _para_ _NCMs_ _com_ _múltiplos_ _enquadramentos_ _(ex:_ _redução_ _60%_ _e_ _100%)._
    -   _Alíquotas_ _e_ _cClassTrib_ _são_ _recalculados_ _dinamicamente_ _baseado_ _na_ _seleção_ _do_ _usuário._

-   **_Persistência_ _de_ _Consulta_**
    -   _Implementado_ `st.session_state` _para_ _manter_ _o_ _estado_ _da_ _consulta_ _ao_ _interagir_ _com_ _widgets._
    -   _Resolve_ _o_ _problema_ _de_ _reset_ _da_ _página_ _ao_ _clicar_ _no_ _seletor_ _de_ _benefícios._
### 🐛 Bug Fixes

-   **_Remoção_ _da_ _Consulta_ _de_ _Inscrição_ _Estadual_ _(IE)_**
    -   _A_ _funcionalidade_ _de_ _consulta_ _de_ _IE_ _foi_ _removida_ _após_ _confirmação_ _de_ _que_ _a_ _API_ _pública_ _da_ _CNPJA_ _não_ _fornece_ _esses_ _dados._
    -   _Código_ _relacionado_ _(funções,_ _UI,_ _exportação)_ _foi_ _completamente_ _removido_ _para_ _evitar_ _erros_ _e_ _confusão_ _do_ _usuário._

-   **_Correção_ _de_ _Cores_ _e_ _Contraste_**
    -   _Corrigido_ _problema_ _de_ _texto_ _branco_ _em_ _fundo_ _branco_ _em_ _diversos_ _componentes._
    -   _Removido_ _CSS_ _complexo_ _e_ _estilos_ _inline_ _que_ _causavam_ _conflitos._
    -   _Ajustada_ _a_ _cor_ _amarela_ _para_ _o_ _padrão_ _PRICETAX_ _(#FFDD00)._

-   **_Correção_ _de_ _NameError_**
    -   _Resolvido_ _erro_ _de_ _variáveis_ _não_ _definidas_ _(`COLOR_SUCCESS`,_ `ncm_clean`,_ `desc_anexo`,_ `beneficio_selecionado`)_ _em_ _diferentes_ _escopos_ _e_ _abas._

-   **_Correção_ _do_ _Mapeamento_ _de_ _cClassTrib_**
    -   _Corrigido_ _mapeamento_ _incorreto_ _que_ _atribuía_ _cClassTrib_ _de_ _alimentos_ _(200034)_ _para_ _outros_ _anexos_ _(ex:_ _ANEXO_ _XI)._

_###_ _📄_ _Documentação_

-   **_README.md_ _Atualizado_**
    -   _Versão_ _atualizada_ _para_ _4.1._
    -   _Estrutura_ _de_ _arquivos_ _e_ _fluxo_ _de_ _classificação_ _atualizados._

-   **_ARCHITECTURE.md_ _Criado_**
    -   _Documentação_ _detalhada_ _da_ _arquitetura,_ _decisões_ _técnicas_ _e_ _fluxos_ _de_ _dados._

-   **_CHANGELOG.md_ _Criado_**
    -   _Este_ _arquivo,_ _para_ _manter_ _um_ _histórico_ _claro_ _das_ _alterações._

_---

_##_ _v4.0_ _(Dezembro_ _2024)_

-   _✅_ _Correção_ _crítica:_ _cClassTrib_ _para_ _cesta_ _básica_ _(200003/200034)_
-   _✅_ _Adição_ _de_ _204_ _sinônimos_ _validados_
-   _✅_ _Enriquecimento_ _de_ _7.887_ _NCMs_ _com_ _hierarquia_ _completa_
-   _✅_ _Integração_ _da_ _base_ _legal_ _LC_ _214/2025_ _(544_ _artigos)_
-   _✅_ _Modularização_ _do_ _código_ _(utils.py,_ _tributacao.py)_
-   _✅_ _Aumento_ _de_ _comentários_ _inline_
-   _✅_ _README.md_ _completo_

_---

_##_ _v3.0_ _(Novembro_ _2024)_

-   _✅_ _Análise_ _de_ _XML_ _NF-e_
-   _✅_ _Coleta_ _silenciosa_ _de_ _dados_ _de_ _mercado_
-   _✅_ _Ranking_ _SPED_

_---

_##_ _v2.0_ _(Outubro_ _2024)_

-   _✅_ _Busca_ _semântica_ _por_ _descrição_
-   _✅_ _Dicionário_ _de_ _sinônimos_

_---

_##_ _v1.0_ _(Setembro_ _2024)_

-   _✅_ _Consulta_ _NCM_ _+_ _CFOP_
-   _✅_ _Consulta_ _CFOP_ _isolada_
-   _✅_ _Base_ _TIPI_ _completa_
