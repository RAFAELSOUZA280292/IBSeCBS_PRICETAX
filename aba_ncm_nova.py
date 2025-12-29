# =============================================================================
# ABA 1 - CONSULTA NCM (VERSÃO REFATORADA COM BUSCA FLEXÍVEL)
# =============================================================================

with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <div class="pricetax-card-header">Consulta Inteligente de Tributação IBS/CBS</div>
            <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                Utilize este painel para consultar a tributação de produtos e operações:<br><br>
                • <strong>Busca por NCM + CFOP:</strong> Informe o NCM e opcionalmente o CFOP<br>
                • <strong>Busca somente por CFOP:</strong> Consulte a tributação padrão da operação<br>
                • <strong>Busca por descrição:</strong> Digite palavras-chave (ex: leite, arroz, computador) e selecione o produto
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Seletor de tipo de busca
    tipo_busca = st.radio(
        "Selecione o tipo de busca:",
        ["NCM + CFOP", "Somente CFOP", "Descrição do Produto"],
        horizontal=True,
    )
    
    # =============================================================================
    # BUSCA POR NCM + CFOP (MODO ORIGINAL)
    # =============================================================================
    if tipo_busca == "NCM + CFOP":
        col1, col2, col3 = st.columns([3, 1.4, 1])
        with col1:
            ncm_input = st.text_input(
                "NCM do produto",
                placeholder="Ex.: 16023220 ou 16.02.32.20",
                help="Informe o NCM completo (8 dígitos), com ou sem pontos.",
            )
        with col2:
            cfop_input = st.text_input(
                "CFOP (opcional)",
                placeholder="Ex.: 5102",
                max_chars=4,
                help="CFOP utilizado na operação (quatro dígitos).",
            )
        with col3:
            st.write("")
            consultar = st.button("Consultar", type="primary")

        if consultar and ncm_input.strip():
            row = buscar_ncm(df_tipi, ncm_input)

            if row is None:
                st.markdown(
                    f"""
                    <div class="pricetax-card-error">
                        <strong>NCM informado:</strong> {ncm_input}<br>
                        Não localizamos esse NCM na base PRICETAX. Revise o código ou a planilha de referência.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # [CÓDIGO EXISTENTE DE EXIBIÇÃO DO RESULTADO - MANTIDO INTACTO]
                # Copiar todo o bloco de exibição do resultado (linhas 970-1187)
                pass  # Placeholder - será substituído pelo código completo
    
    # =============================================================================
    # BUSCA SOMENTE POR CFOP
    # =============================================================================
    elif tipo_busca == "Somente CFOP":
        col1, col2 = st.columns([2, 1])
        with col1:
            cfop_input = st.text_input(
                "CFOP da operação",
                placeholder="Ex.: 5102",
                max_chars=4,
                help="Informe o CFOP da operação (quatro dígitos).",
            )
        with col2:
            st.write("")
            consultar_cfop = st.button("Consultar CFOP", type="primary")
        
        if consultar_cfop and cfop_input.strip():
            import os
            arquivo_cfop = os.path.join(os.path.dirname(__file__), "CFOP_CCLASSTRIB.xlsx")
            
            try:
                df_cfop = pd.read_excel(arquivo_cfop, sheet_name="Correlação", skiprows=2)
                cfop_clean = int(re.sub(r"\D+", "", cfop_input))
                
                resultado = df_cfop[df_cfop["CFOP"] == cfop_clean]
                
                if len(resultado) == 0:
                    st.markdown(
                        f"""
                        <div class="pricetax-card-error">
                            <strong>CFOP informado:</strong> {cfop_input}<br>
                            Não localizamos esse CFOP na base PRICETAX.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    reg = resultado.iloc[0]
                    
                    st.markdown(
                        f"""
                        <div class="pricetax-card" style="margin-top:1.5rem;">
                            <div style="font-size:1.3rem;font-weight:600;color:{COLOR_GOLD};margin-bottom:1rem;">
                                CFOP {cfop_clean} - {reg['Tipo']}
                            </div>
                            <div style="font-size:1rem;color:{COLOR_WHITE};margin-bottom:1rem;">
                                {reg['Descrição Resumida']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    st.markdown("### Tributação Padrão da Operação")
                    
                    col_cfop1, col_cfop2, col_cfop3, col_cfop4 = st.columns(4)
                    
                    with col_cfop1:
                        st.markdown(f"**Operação Onerosa:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['Operação Onerosa?']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop2:
                        st.markdown(f"**Incide IBS/CBS:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['Incide IBS/CBS']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop3:
                        st.markdown(f"**CST IBS/CBS:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['CST IBS/CBS']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop4:
                        st.markdown(f"**cClassTrib:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['cClassTrib']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("### Alíquotas Padrão")
                    
                    st.markdown(
                        f"""
                        <div class="metric-container">
                            <div class="metric-box">
                                <div class="metric-label">IBS Padrão</div>
                                <div class="metric-value">{pct_str(reg['ALIQ. IBS'])}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">CBS Padrão</div>
                                <div class="metric-value">{pct_str(reg['ALIQ.CBS'])}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Carga Total</div>
                                <div class="metric-value">{pct_str(reg['ALIQ. IBS'] + reg['ALIQ.CBS'])}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    st.info("Esta é a tributação padrão do CFOP. Para produtos específicos com reduções ou regimes especiais, utilize a busca por NCM.")
                    
            except Exception as e:
                st.error(f"Erro ao carregar planilha CFOP: {str(e)}")
    
    # =============================================================================
    # BUSCA POR DESCRIÇÃO (SEMÂNTICA)
    # =============================================================================
    elif tipo_busca == "Descrição do Produto":
        col1, col2 = st.columns([3, 1])
        with col1:
            desc_input = st.text_input(
                "Descrição ou palavras-chave",
                placeholder="Ex.: leite em pó, arroz integral, notebook",
                help="Digite palavras-chave para buscar produtos na TIPI.",
            )
        with col2:
            st.write("")
            buscar_desc = st.button("Buscar", type="primary")
        
        if buscar_desc and desc_input.strip():
            # Busca semântica na descrição
            termos = desc_input.strip().lower().split()
            
            # Filtrar produtos que contenham TODOS os termos
            mask = df_tipi["NCM_DESCRICAO"].str.lower().str.contains(termos[0], na=False)
            for termo in termos[1:]:
                mask = mask & df_tipi["NCM_DESCRICAO"].str.lower().str.contains(termo, na=False)
            
            resultados = df_tipi[mask]
            
            if len(resultados) == 0:
                st.markdown(
                    f"""
                    <div class="pricetax-card-error">
                        <strong>Busca:</strong> {desc_input}<br>
                        Nenhum produto encontrado com esses termos. Tente palavras-chave diferentes.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif len(resultados) == 1:
                # Apenas 1 resultado - exibir diretamente
                row = resultados.iloc[0]
                st.success(f"1 produto encontrado: {row['NCM_DESCRICAO']}")
                
                # [CÓDIGO DE EXIBIÇÃO DO RESULTADO - MESMO DO MODO NCM]
                # Copiar bloco de exibição (linhas 970-1187)
                pass  # Placeholder
                
            else:
                # Múltiplos resultados - lista de seleção
                st.success(f"{len(resultados)} produtos encontrados. Selecione o produto desejado:")
                
                # Criar lista de opções
                opcoes = []
                for idx, row in resultados.iterrows():
                    ncm_fmt = row["NCM_DIG"]
                    desc = row["NCM_DESCRICAO"]
                    opcoes.append(f"{ncm_fmt} - {desc}")
                
                produto_selecionado = st.selectbox(
                    "Produtos encontrados:",
                    opcoes,
                    help="Selecione o produto correto da lista.",
                )
                
                if produto_selecionado:
                    # Extrair NCM da seleção
                    ncm_selecionado = produto_selecionado.split(" - ")[0]
                    row = resultados[resultados["NCM_DIG"] == ncm_selecionado].iloc[0]
                    
                    # Solicitar CFOP opcional
                    cfop_input = st.text_input(
                        "CFOP (opcional)",
                        placeholder="Ex.: 5102",
                        max_chars=4,
                        help="Informe o CFOP para sugestão de cClassTrib.",
                    )
                    
                    # [CÓDIGO DE EXIBIÇÃO DO RESULTADO - MESMO DO MODO NCM]
                    # Copiar bloco de exibição (linhas 970-1187)
                    pass  # Placeholder
