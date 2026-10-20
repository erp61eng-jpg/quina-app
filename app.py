import streamlit as st
import pandas as pd
import re
import io

# Configuração da página para a Quina
st.set_page_config(
    page_title="Filtrador de Jogos da Quina - Termômetro de Dezenas",
    page_icon="🎯",
    layout="wide"
)

# Estilização CSS para as dezenas circulares coloridas da Quina
st.markdown("""
<style>
    .dezena-box {
        display: inline-block;
        width: 38px;
        height: 38px;
        line-height: 38px;
        text-align: center;
        border-radius: 50%;
        margin: 2px 3px;
        font-weight: 700;
        font-size: 13px;
        color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .quente { 
        background-color: #d63031 !important; 
        border: 2px solid #ff7675;
    }
    .media { 
        background-color: #e67e22 !important; 
        border: 2px solid #f39c12;
    }
    .fria { 
        background-color: #0984e3 !important; 
        border: 2px solid #74b9ff;
    }
    .card-jogo {
        background-color: #1e272e;
        border: 1px solid #3d4a54;
        border-radius: 8px;
        padding: 8px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .info-jogo {
        color: #dcdde1;
        font-size: 13px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Filtrador de Jogos da Quina com Cores Térmicas")
st.write("Processamento e filtragem de combinações da Quina (dezenas de 01 a 80) por volume de frequência e temperatura.")

# =====================================================================
# FUNÇÕES DE EXTRAÇÃO E PROCESSAMENTO (QUINA: 01 A 80)
# =====================================================================
def extrair_jogos_quina(conteudo: str) -> list[list[int]]:
    """Extrai jogos da Quina: números válidos estritamente entre 1 e 80, mínimo de 5 dezenas."""
    jogos = []
    for linha in conteudo.splitlines():
        numeros = [int(n) for n in re.findall(r'\b\d{1,2}\b', linha)]
        # Filtra estritamente dezenas válidas da Quina (1 a 80) e remove duplicatas na mesma linha
        dezenas_validas = sorted(list(set([n for n in numeros if 1 <= n <= 80])))
        if len(dezenas_validas) >= 5:
            jogos.append(dezenas_validas)
    return jogos

# =====================================================================
# SEÇÃO 1: UPLOAD DE ARQUIVOS (CENTRO DA TELA)
# =====================================================================
st.subheader("📂 1. Upload dos Arquivos da Quina")

col_arq1, col_arq2 = st.columns(2)

with col_arq1:
    upload_jogos = st.file_uploader(
        "👉 SELECIONE O ARQUIVO DE JOGOS DA QUINA (.txt ou .csv):",
        type=["txt", "csv"],
        key="upload_jogos_quina",
        help="Arquivo contendo as combinações geradas da Quina (mínimo de 5 dezenas de 01 a 80 por linha)."
    )

with col_arq2:
    upload_historico = st.file_uploader(
        "📊 HISTÓRICO DE RESULTADOS DA QUINA (Opcional):",
        type=["txt", "csv"],
        key="upload_historico_quina",
        help="Resultados oficiais anteriores para basear a contagem térmica. Se vazio, o cálculo usará o próprio arquivo de jogos."
    )

st.write("---")

# =====================================================================
# SEÇÃO 2: EXECUÇÃO DO PROCESSAMENTO E FILTROS
# =====================================================================
if upload_jogos is not None:
    conteudo_jogos = upload_jogos.getvalue().decode("utf-8", errors="ignore")
    jogos_brutos = extrair_jogos_quina(conteudo_jogos)
    
    if not jogos_brutos:
        st.error("Nenhuma linha com 5 ou mais dezenas válidas (entre 01 e 80) foi encontrada no arquivo enviado.")
        st.stop()

    # Cálculo da frequência sobre a base definida
    if upload_historico is not None:
        conteudo_hist = upload_historico.getvalue().decode("utf-8", errors="ignore")
        jogos_base = extrair_jogos_quina(conteudo_hist)
        origem_dados = f"Histórico Quina ({len(jogos_base)} sorteios)"
    else:
        jogos_base = jogos_brutos
        origem_dados = f"Próprio arquivo de jogos ({len(jogos_brutos)} combinações)"

    todas_dezenas = [d for jogo in jogos_base for d in jogo]
    freq = pd.Series(todas_dezenas).value_counts()

    # Faixas térmicas por tercis
    corte_quente = freq.quantile(0.66)
    corte_medio = freq.quantile(0.33)

    dezenas_quentes = set(freq[freq >= corte_quente].index)
    dezenas_frias = set(freq[freq < corte_medio].index)
    dezenas_medias = set(freq[(freq >= corte_medio) & (freq < corte_quente)].index)

    # Painel de Filtros na barra lateral
    st.sidebar.header("⚙️ Filtros para Quina")
    st.sidebar.caption(f"Frequência baseada em: **{origem_dados}**")
    
    max_dezenas_jogo = max(len(j) for j in jogos_brutos)

    filtro_quentes = st.sidebar.slider(
        "🔴 Dezenas QUENTES por aposta:",
        min_value=0,
        max_value=max_dezenas_jogo,
        value=(1, max_dezenas_jogo)
    )

    filtro_medias = st.sidebar.slider(
        "🟠 Dezenas MÉDIAS por aposta:",
        min_value=0,
        max_value=max_dezenas_jogo,
        value=(0, max_dezenas_jogo)
    )

    filtro_frias = st.sidebar.slider(
        "🔵 Dezenas FRIAS por aposta:",
        min_value=0,
        max_value=max_dezenas_jogo,
        value=(0, max_dezenas_jogo)
    )

    filtro_pares_ativo = st.sidebar.checkbox("Ativar filtro de PARES", value=False)
    if filtro_pares_ativo:
        filtro_pares = st.sidebar.slider(
            "Quantidade de dezenas PARES:",
            min_value=0,
            max_value=max_dezenas_jogo,
            value=(2, 3)
        )

    # Filtragem das combinações
    jogos_filtrados = []
    for jogo in jogos_brutos:
        qtd_q = sum(1 for d in jogo if d in dezenas_quentes)
        qtd_m = sum(1 for d in jogo if d in dezenas_medias)
        qtd_f = sum(1 for d in jogo if d in dezenas_frias)
        qtd_pares = sum(1 for d in jogo if d % 2 == 0)

        passou = (
            filtro_quentes[0] <= qtd_q <= filtro_quentes[1] and
            filtro_medias[0] <= qtd_m <= filtro_medias[1] and
            filtro_frias[0] <= qtd_f <= filtro_frias[1]
        )

        if filtro_pares_ativo and passou:
            passou = filtro_pares[0] <= qtd_pares <= filtro_pares[1]

        if passou:
            jogos_filtrados.append({
                "jogo": jogo,
                "quentes": qtd_q,
                "medias": qtd_m,
                "frias": qtd_f,
                "pares": qtd_pares
            })

    # =====================================================================
    # SEÇÃO 3: RESULTADOS E MAPA TÉRMICO (01 A 80)
    # =====================================================================
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total no Arquivo", len(jogos_brutos))
    m2.metric("Jogos Aprovados", len(jogos_filtrados))
    m3.metric("Jogos Eliminados", len(jogos_brutos) - len(jogos_filtrados))
    taxa = (len(jogos_filtrados) / len(jogos_brutos)) * 100 if jogos_brutos else 0
    m4.metric("Taxa de Retenção", f"{taxa:.1f}%")

    st.write("---")

    # Exibição do universo de dezenas classificadas
    st.subheader("🔥 Mapa de Temperatura das Dezenas da Quina")

    def gerar_html_dezenas(grupo_dezenas, classe_css):
        html = ""
        for d in sorted(grupo_dezenas):
            html += f'<span class="dezena-box {classe_css}">{d:02d}</span>'
        return html

    st.markdown(f"**🔴 Quentes ({len(dezenas_quentes)} dezenas):**", unsafe_allow_html=True)
    st.markdown(gerar_html_dezenas(dezenas_quentes, "quente"), unsafe_allow_html=True)

    st.markdown(f"**🟠 Médias ({len(dezenas_medias)} dezenas):**", unsafe_allow_html=True)
    st.markdown(gerar_html_dezenas(dezenas_medias, "media"), unsafe_allow_html=True)

    st.markdown(f"**🔵 Frias ({len(dezenas_frias)} dezenas):**", unsafe_allow_html=True)
    st.markdown(gerar_html_dezenas(dezenas_frias, "fria"), unsafe_allow_html=True)

    st.write("---")

    # Amostragem dos jogos da Quina aprovados
    st.subheader(f"📋 Apostas da Quina Aprovadas ({len(jogos_filtrados)} jogos)")

    limite_exibicao = 50
    for idx, item in enumerate(jogos_filtrados[:limite_exibicao]):
        html_linha = '<div class="card-jogo"><div>'
        html_linha += f'<span style="color:#8395a7; margin-right: 12px; font-weight: bold;">#{idx+1:03d}</span>'
        
        for d in item["jogo"]:
            if d in dezenas_quentes:
                css = "quente"
            elif d in dezenas_medias:
                css = "media"
            else:
                css = "fria"
            html_linha += f'<span class="dezena-box {css}">{d:02d}</span>'
            
        html_linha += '</div>'
        html_linha += f'<div class="info-jogo">🔴 {item["quentes"]} | 🟠 {item["medias"]} | 🔵 {item["frias"]} | Pares: {item["pares"]}</div>'
        html_linha += '</div>'
        st.markdown(html_linha, unsafe_allow_html=True)

    if len(jogos_filtrados) > limite_exibicao:
        st.info(f"Mostrando os primeiros {limite_exibicao} jogos na tela para estabilidade visual. O arquivo exportado abaixo contém todos os {len(jogos_filtrados)} jogos aprovados.")

    # =====================================================================
    # SEÇÃO 4: DOWNLOAD DO ARQUIVO DA QUINA FILTRADO
    # =====================================================================
    texto_saida = "\n".join([" ".join(f"{d:02d}" for d in item["jogo"]) for item in jogos_filtrados])
    
    st.download_button(
        label="📥 Baixar Jogos da Quina Filtrados (.txt)",
        data=texto_saida,
        file_name="quina_filtrada.txt",
        mime="text/plain"
    )

else:
    st.info("Envie seu arquivo de jogos da Quina no campo acima para processar as dezenas e aplicar os filtros.")
