import streamlit as st
import random
from itertools import combinations
from collections import defaultdict, Counter
import pandas as pd

st.set_page_config(
    page_title="Quina - Laboratório & Fechamentos",
    page_icon="🎯",
    layout="wide"
)

# ==============================================================================
# 1. BASE HISTÓRICA DOS ÚLTIMOS 30 SORTEIOS DA QUINA
# ==============================================================================
HISTORICO_30_QUINA = [
    [5, 18, 32, 54, 76], [12, 23, 44, 59, 71], [3, 27, 39, 61, 80],
    [9, 14, 38, 52, 68], [1, 22, 35, 47, 73], [16, 29, 41, 58, 65],
    [7, 31, 48, 63, 79], [11, 25, 36, 50, 77], [4, 19, 42, 55, 69],
    [8, 20, 33, 60, 74], [15, 28, 46, 57, 70], [2, 17, 37, 53, 78],
    [10, 24, 40, 62, 75], [6, 21, 45, 56, 72], [13, 30, 49, 64, 80],
    [5, 26, 43, 51, 67], [18, 34, 47, 66, 79], [9, 23, 39, 58, 71],
    [14, 27, 44, 61, 76], [3, 16, 35, 52, 68], [1, 29, 42, 59, 74],
    [12, 32, 48, 65, 80], [7, 22, 38, 54, 73], [19, 31, 46, 60, 77],
    [4, 25, 41, 57, 70], [11, 28, 45, 63, 78], [8, 17, 36, 50, 69],
    [15, 20, 37, 53, 75], [2, 24, 40, 56, 72], [10, 21, 43, 62, 76]
]

TOTAL_NUMS = 80
TAMANHO_JOGO = 5
QTD_LINHAS = 8

# ==============================================================================
# 2. MAPEAMENTO MATEMÁTICO DA MATRIZ 8x10 (80 DEZENAS)
# ==============================================================================
@st.cache_data
def get_primos_quina():
    cands = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79]
    return [p for p in cands if p <= TOTAL_NUMS]

@st.cache_data
def get_moldura_quina():
    mold = set(range(1, 11)) | set(range(71, 81))
    for r in range(8):
        mold.add(r * 10 + 1)
        mold.add(r * 10 + 10)
    return sorted(list(mold))

@st.cache_data
def get_diagonais_direita_quina():
    return {
        f"Diag Direita {c+1:02d}": sorted([(r * 10) + ((c + r) % 10) + 1 for r in range(8)])
        for c in range(10)
    }

@st.cache_data
def get_diagonais_esquerda_quina():
    return {
        f"Diag Esquerda {c+1:02d}": sorted([(r * 10) + ((c - r) % 10) + 1 for r in range(8)])
        for c in range(10)
    }

# ==============================================================================
# 3. INICIALIZAÇÃO DE ESTADO
# ==============================================================================
if "grupos_base" not in st.session_state:
    grupos = {
        "Pares": [n for n in range(1, 81) if n % 2 == 0],
        "Ímpares": [n for n in range(1, 81) if n % 2 != 0],
        "Primos": get_primos_quina(),
        "Moldura": get_moldura_quina(),
        "Centro (Miolo)": [n for n in range(1, 81) if n not in get_moldura_quina()]
    }
    for l in range(8):
        grupos[f"Linha {l+1}"] = list(range(l * 10 + 1, (l + 1) * 10 + 1))
    for c in range(10):
        grupos[f"Coluna {c+1}"] = [r * 10 + c + 1 for r in range(8)]
        
    grupos.update(get_diagonais_direita_quina())
    grupos.update(get_diagonais_esquerda_quina())
    st.session_state.grupos_base = grupos

if "regras_ativas" not in st.session_state:
    regras = {}
    for k in st.session_state.grupos_base.keys():
        regras[k] = {"ativo": False, "min": 0, "max": 2}
    
    regras["Pares"] = {"ativo": True, "min": 2, "max": 3}
    regras["Primos"] = {"ativo": True, "min": 0, "max": 2}
    regras["Moldura"] = {"ativo": True, "min": 1, "max": 4}
    st.session_state.regras_ativas = regras

if "filtro_soma_ativo" not in st.session_state: st.session_state.filtro_soma_ativo = True
if "faixa_soma" not in st.session_state: st.session_state.faixa_soma = (140, 265)
if "filtro_consec_ativo" not in st.session_state: st.session_state.filtro_consec_ativo = True
if "max_consec" not in st.session_state: st.session_state.max_consec = 1

if "historico_sorteios" not in st.session_state:
    st.session_state.historico_sorteios = [list(j) for j in HISTORICO_30_QUINA]
if "f_rep_ant_ativo" not in st.session_state: st.session_state.f_rep_ant_ativo = True
if "rep_ant_faixa" not in st.session_state: st.session_state.rep_ant_faixa = (0, 1)
if "f_max_coinc_ativo" not in st.session_state: st.session_state.f_max_coinc_ativo = True
if "max_coinc_30" not in st.session_state: st.session_state.max_coinc_30 = 3
if "f_freq_30_ativo" not in st.session_state: st.session_state.f_freq_30_ativo = False
if "faixa_quentes" not in st.session_state: st.session_state.faixa_quentes = (1, 3)
if "faixa_frias" not in st.session_state: st.session_state.faixa_frias = (0, 2)

if "jogos_aleatorios" not in st.session_state: st.session_state.jogos_aleatorios = []
if "jogos_fechamento" not in st.session_state: st.session_state.jogos_fechamento = []

# ==============================================================================
# 4. PROCESSAMENTO ESTATÍSTICO & VALIDAÇÕES
# ==============================================================================
def processar_frequencia(historico):
    cnt = Counter()
    for j in historico: cnt.update(j)
    nums = sorted(range(1, 81), key=lambda d: cnt[d], reverse=True)
    c1, c2 = 27, 54
    return set(nums[:c1]), set(nums[c1:c2]), set(nums[c2:]), cnt

def contar_consecutivos(jogo):
    maior = seq = 1
    for i in range(len(jogo) - 1):
        if jogo[i+1] == jogo[i] + 1:
            seq += 1
            if seq > maior: maior = seq
        else:
            seq = 1
    return maior

def validar_jogo(cand, cand_set, regras_compiladas, f_soma, r_soma, f_consec, m_consec,
                 f_rep, r_rep, ult_set, f_coinc, max_c, hist_sets,
                 f_freq, r_q, r_f, s_q, s_f):
    if f_soma and not (r_soma[0] <= sum(cand) <= r_soma[1]):
        return False
    if f_consec and contar_consecutivos(cand) > m_consec:
        return False
    for g_set, mn, mx in regras_compiladas:
        qtd = len(cand_set & g_set)
        if qtd < mn or qtd > mx:
            return False
    if f_rep and ult_set:
        rep = len(cand_set & ult_set)
        if not (r_rep[0] <= rep <= r_rep[1]):
            return False
    if f_coinc and hist_sets:
        for pass_set in hist_sets:
            if len(cand_set & pass_set) > max_c:
                return False
    if f_freq:
        if not (r_q[0] <= len(cand_set & s_q) <= r_q[1]): return False
        if not (r_f[0] <= len(cand_set & s_f) <= r_f[1]): return False
    return True

def gerar_fechamento_guloso(dezenas, garantia):
    k_alvo = 3 if "Terno" in garantia else 4
    nums = sorted(dezenas)
    alvos_totais = set(combinations(nums, k_alvo))
    total_alvos = len(alvos_totais)
    candidatos = list(combinations(nums, 5))
    if not candidatos: return [], 0.0

    cand_alvos = {c: set(combinations(c, k_alvo)) for c in candidatos}
    alvo_para_cands = defaultdict(list)
    for c, sub in cand_alvos.items():
        for a in sub: alvo_para_cands[a].append(c)

    ganhos = {c: len(sub) for c, sub in cand_alvos.items()}
    alvos_restantes = set(alvos_totais)
    escolhidos = []

    while alvos_restantes:
        melhor = max(ganhos, key=ganhos.get)
        if ganhos[melhor] == 0: break
        escolhidos.append(sorted(list(melhor)))
        novos = cand_alvos[melhor] & alvos_restantes
        alvos_restantes -= novos
        for a in novos:
            for c in alvo_para_cands[a]: ganhos[c] -= 1
        ganhos[melhor] = -1

    taxa = ((total_alvos - len(alvos_restantes)) / total_alvos) * 100 if total_alvos else 100.0
    return escolhidos, taxa

def converter_para_txt(jogos):
    return "\n".join([" ".join([f"{n:02d}" for n in j]) for j in jogos])

# ==============================================================================
# 5. VOLANTE OFICIAL 8x10
# ==============================================================================
def renderizar_volante_8x10(jogo, titulo=""):
    marcadas = set(jogo)
    grid_html = f"""
    <style>
        .volante-box {{ background:#ffffff; border:2px solid #2e7d32; border-radius:10px; padding:14px; width:fit-content; margin:8px auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .volante-grid {{ display:grid; grid-template-columns:repeat(10, 36px); gap:5px; }}
        .v-cell {{ width:36px; height:36px; border:1px solid #dcdcdc; border-radius:6px; display:flex; align-items:center; justify-content:center; font-family:monospace; font-size:12px; color:#555; background:#fafafa; font-weight:500; }}
        .v-marcada {{ background:linear-gradient(135deg, #1b5e20, #2e7d32) !important; color:#ffffff !important; border:2px solid #0b4317 !important; font-weight:bold; transform:scale(1.05); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
    </style>
    <div class="volante-box">
    """
    if titulo:
        grid_html += f"<p style='font-weight:700; font-size:15px; margin-bottom:10px; color:#1b5e20; text-align:center;'>{titulo}</p>"
    grid_html += '<div class="volante-grid">'
    for r in range(8):
        for c in range(10):
            num = r * 10 + c + 1
            cls = "v-cell v-marcada" if num in marcadas else "v-cell"
            grid_html += f'<div class="{cls}">{num:02d}</div>'
    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# ==============================================================================
# 6. INTERFACE PRINCIPAL DA QUINA
# ==============================================================================
st.title("🎯 Quina: Laboratório & Fechamentos")
st.caption("Matriz Oficial 8x10 • Apostas de 5 Dezenas • Restrições Estruturais e Diagonais Cilíndricas.")

tab_filtros, tab_hist, tab_gerador, tab_fechamento, tab_volante = st.tabs([
    "⚙️ Filtros e Padrões",
    "📜 30 Concursos",
    "🚀 Gerador de Jogos",
    "🎯 Fechamentos (Quadra/Terno)",
    "🗺️ Volante Visual 8x10"
])

quentes_30, medias_30, frias_30, freq_cnt = processar_frequencia(st.session_state.historico_sorteios)
hist_sets = [set(j) for j in st.session_state.historico_sorteios]
ult_set = set(st.session_state.historico_sorteios[-1]) if st.session_state.historico_sorteios else set()

# ABA 1: FILTROS
with tab_filtros:
    st.subheader("1. Parâmetros Globais")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.filtro_soma_ativo = st.checkbox("Filtrar por Soma das 5 Dezenas", value=st.session_state.filtro_soma_ativo)
        if st.session_state.filtro_soma_ativo:
            st.session_state.faixa_soma = st.slider("Intervalo de Soma:", 15, 390, st.session_state.faixa_soma)
    with c2:
        st.session_state.filtro_consec_ativo = st.checkbox("Limitar Números Consecutivos", value=st.session_state.filtro_consec_ativo)
        if st.session_state.filtro_consec_ativo:
            st.session_state.max_consec = st.slider("Máximo consecutivo permitido:", 1, 3, st.session_state.max_consec)

    st.divider()
    st.subheader("2. Restrições do Histórico (Últimos 30 Sorteios)")
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.session_state.f_rep_ant_ativo = st.checkbox("Repetição do Último Concurso", value=st.session_state.f_rep_ant_ativo)
        if st.session_state.f_rep_ant_ativo:
            st.session_state.rep_ant_faixa = st.slider("Dezenas repetidas:", 0, 5, st.session_state.rep_ant_faixa)
            st.caption(f"Último sorteio: {sorted(list(ult_set))}")
    with ch2:
        st.session_state.f_max_coinc_ativo = st.checkbox("Teto de Coincidência Histórica", value=st.session_state.f_max_coinc_ativo)
        if st.session_state.f_max_coinc_ativo:
            st.session_state.max_coinc_30 = st.slider("Máx. acertos repetidos nos 30 concursos:", 2, 4, st.session_state.max_coinc_30)
    with ch3:
        st.session_state.f_freq_30_ativo = st.checkbox("Equilíbrio Quentes / Frias", value=st.session_state.f_freq_30_ativo)
        if st.session_state.f_freq_30_ativo:
            st.session_state.faixa_quentes = st.slider("Top Quentes:", 0, 5, st.session_state.faixa_quentes)
            st.session_state.faixa_frias = st.slider("Mais Atrasadas (Frias):", 0, 5, st.session_state.faixa_frias)

    st.divider()
    st.subheader("3. Padrões Clássicos e Diagonais Cilíndricas (8x10)")
    
    with st.expander("📌 Padrões Matriciais (Pares, Primos, Moldura)"):
        for padrao in ["Pares", "Primos", "Moldura", "Centro (Miolo)"]:
            col_chk, col_sl = st.columns([2, 3])
            with col_chk:
                st.session_state.regras_ativas[padrao]["ativo"] = st.checkbox(padrao, value=st.session_state.regras_ativas[padrao]["ativo"], key=f"c_{padrao}")
            with col_sl:
                if st.session_state.regras_ativas[padrao]["ativo"]:
                    v = st.slider(f"Qtd {padrao}", 0, 5, (st.session_state.regras_ativas[padrao]["min"], st.session_state.regras_ativas[padrao]["max"]), key=f"s_{padrao}")
                    st.session_state.regras_ativas[padrao]["min"], st.session_state.regras_ativas[padrao]["max"] = v

    diag_dir = [f"Diag Direita {i:02d}" for i in range(1, 11)]
    diag_esq = [f"Diag Esquerda {i:02d}" for i in range(1, 11)]
    
    with st.expander("↘️ 10 Diagonais Direitas da Quina (8 dezenas cada)"):
        for k in diag_dir:
            chk, sl = st.columns([2, 3])
            with chk:
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(k, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"]), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

    with st.expander("↙️ 10 Diagonais Esquerdas da Quina (8 dezenas cada)"):
        for k in diag_esq:
            chk, sl = st.columns([2, 3])
            with chk:
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(k, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"]), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

# ABA 2: HISTÓRICO
with tab_hist:
    st.subheader("Base Atual: 30 Últimos Concursos")
    col_hist1, col_hist2 = st.columns([3, 2])
    with col_hist1:
        dados_tabela = [
            {"Concurso": f"#{30-idx:02d}", "Dezenas": " - ".join([f"{n:02d}" for n in s]), "Soma": sum(s)}
            for idx, s in enumerate(reversed(st.session_state.historico_sorteios))
        ]
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, height=450)
    with col_hist2:
        st.markdown("**Top 10 Mais Frequentes (Últimos 30):**")
        top_10 = sorted(freq_cnt.items(), key=lambda x: x[1], reverse=True)[:10]
        st.write(", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in top_10]))
        st.markdown("**Top 10 Menos Frequentes (Atrasadas):**")
        bot_10 = sorted(freq_cnt.items(), key=lambda x: x[1])[:10]
        st.write(", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in bot_10]))

# ABA 3: GERADOR
with tab_gerador:
    st.subheader("Gerar Combinações Validadas (5 Dezenas)")
    qtd = st.number_input("Quantidade de Jogos Desejada:", min_value=1, max_value=200, value=5)
    
    if st.button("Gerar Apostas da Quina 🚀", use_container_width=True):
        regras_comp = [(frozenset(st.session_state.grupos_base[k]), v["min"], v["max"]) for k, v in st.session_state.regras_ativas.items() if v["ativo"]]
        jogos, unicos, t = [], set(), 0
        pool = list(range(1, 81))
        
        with st.spinner("Filtrando combinações..."):
            while len(jogos) < qtd and t < 250_000:
                c = sorted(random.sample(pool, 5))
                ctup = tuple(c)
                if ctup not in unicos:
                    if validar_jogo(c, set(c), regras_comp,
                                    st.session_state.filtro_soma_ativo, st.session_state.faixa_soma,
                                    st.session_state.filtro_consec_ativo, st.session_state.max_consec,
                                    st.session_state.f_rep_ant_ativo, st.session_state.rep_ant_faixa, ult_set,
                                    st.session_state.f_max_coinc_ativo, st.session_state.max_coinc_30, hist_sets,
                                    st.session_state.f_freq_30_ativo, st.session_state.faixa_quentes, st.session_state.faixa_frias,
                                    quentes_30, frias_30):
                        jogos.append(c)
                        unicos.add(ctup)
                t += 1
                
        st.session_state.jogos_aleatorios = jogos
        if not jogos:
            st.error("Nenhum jogo cumpriu todos os critérios com 250.000 iterações. Tente afrouxar os filtros na Aba 1.")

    if st.session_state.jogos_aleatorios:
        st.success(f"{len(st.session_state.jogos_aleatorios)} aposta(s) gerada(s):")
        
        c_down1, c_down2 = st.columns([1, 1])
        with c_down1:
            st.download_button(
                "📥 Baixar Jogos em TXT",
                data=converter_para_txt(st.session_state.jogos_aleatorios),
                file_name="apostas_quina.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        for i, j in enumerate(st.session_state.jogos_aleatorios):
            st.code(f"Jogo #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])}  |  Soma: {sum(j)}")

# ABA 4: FECHAMENTO
with tab_fechamento:
    st.subheader("Fechamentos Matemáticos (Desdobramento Guloso)")
    dezs = st.multiselect(
        "Selecione de 7 a 20 dezenas base:", 
        options=list(range(1, 81)), 
        default=list(range(1, 11)), 
        format_func=lambda x: f"{x:02d}"
    )
    gar = st.selectbox("Garantia Matemática pretendida:", ["Quadra (Garante 4 se acertar 5)", "Terno (Garante 3 se acertar 5)"])
    
    if len(dezs) >= 6:
        if st.button("Calcular Matriz Fechada 🧮", use_container_width=True):
            with st.spinner("Calculando cobertura combinatória..."):
                j_fech, cob = gerar_fechamento_guloso(dezs, gar)
                st.session_state.jogos_fechamento = j_fech
                st.session_state.taxa_cobertura = cob
    else:
        st.info("Selecione pelo menos 6 dezenas para processar um fechamento.")

    if st.session_state.jogos_fechamento:
        st.success(f"Fechamento: {len(st.session_state.jogos_fechamento)} jogos gerados (Cobertura: {st.session_state.get('taxa_cobertura', 100):.1f}%)")
        
        st.download_button(
            "📥 Baixar Fechamento em TXT",
            data=converter_para_txt(st.session_state.jogos_fechamento),
            file_name="fechamento_quina.txt",
            mime="text/plain"
        )
        for i, j in enumerate(st.session_state.jogos_fechamento):
            st.code(f"Aposta #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])}")

# ABA 5: VOLANTE
with tab_volante:
    st.subheader("Visualizador da Cartela Oficial 8x10")
    
    opcoes_visualizacao = ["Cartela Vazia"]
    if st.session_state.jogos_aleatorios:
        opcoes_visualizacao.extend([f"Gerador - Jogo #{i+1:02d}" for i in range(len(st.session_state.jogos_aleatorios))])
    if st.session_state.jogos_fechamento:
        opcoes_visualizacao.extend([f"Fechamento - Jogo #{i+1:02d}" for i in range(len(st.session_state.jogos_fechamento))])
    
    escolha = st.selectbox("Selecione um jogo para mapear no volante:", opcoes_visualizacao)
    
    jogo_exibir = []
    if "Gerador" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_aleatorios[idx]
    elif "Fechamento" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_fechamento[idx]
        
    renderizar_volante_8x10(jogo_exibir, titulo=escolha)