import streamlit as st
import random
import re
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
    """10 diagonais cilíndricas (+11 mod 10) de 8 dezenas cada"""
    return {
        f"Diag Direita {c+1:02d}": sorted([(r * 10) + ((c + r) % 10) + 1 for r in range(8)])
        for c in range(10)
    }

@st.cache_data
def get_diagonais_esquerda_quina():
    """10 diagonais cilíndricas (+9 mod 10) de 8 dezenas cada"""
    return {
        f"Diag Esquerda {c+1:02d}": sorted([(r * 10) + ((c - r) % 10) + 1 for r in range(8)])
        for c in range(10)
    }

def construir_todos_grupos():
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
    return grupos

# ==============================================================================
# 3. MOTOR ESTATÍSTICO DINÂMICO DOS 30 SORTEIOS
# ==============================================================================
def contar_consecutivos(jogo):
    maior = seq = 1
    for i in range(len(jogo) - 1):
        if jogo[i+1] == jogo[i] + 1:
            seq += 1
            if seq > maior: maior = seq
        else:
            seq = 1
    return maior

def processar_estatisticas_completas(historico, grupos_base):
    # 1. Contagem de frequência individual
    cnt_dezenas = Counter()
    for s in historico: cnt_dezenas.update(s)
    ordenados_freq = sorted(range(1, 81), key=lambda d: (cnt_dezenas[d], -d), reverse=True)
    quentes = set(ordenados_freq[:27])
    medias = set(ordenados_freq[27:54])
    frias = set(ordenados_freq[54:])

    # 2. Estatísticas de Soma
    somas = [sum(s) for s in historico]
    min_soma = min(somas) if somas else 15
    max_soma = max(somas) if somas else 390
    media_soma = sum(somas) / len(somas) if somas else 202.5

    # 3. Estatísticas de Consecutivos
    consecs = [contar_consecutivos(s) for s in historico]
    max_consec = max(consecs) if consecs else 1

    # 4. Repetição em relação ao sorteio anterior
    reps = []
    for i in range(1, len(historico)):
        reps.append(len(set(historico[i]) & set(historico[i-1])))
    min_rep = min(reps) if reps else 0
    max_rep = max(reps) if reps else 1

    # 5. Estatísticas de CADA grupo (especialmente as 20 Diagonais)
    stats_grupos = {}
    for nome, dezenas in grupos_base.items():
        dez_set = set(dezenas)
        ocorrencias = [len(set(s) & dez_set) for s in historico]
        stats_grupos[nome] = {
            "min": min(ocorrencias) if ocorrencias else 0,
            "max": max(ocorrencias) if ocorrencias else 5,
            "media": sum(ocorrencias) / len(ocorrencias) if ocorrencias else 0.0,
            "total_saidas": sum(ocorrencias),
            "distribuicao": Counter(ocorrencias),
            "dezenas": dezenas
        }

    return {
        "cnt_dezenas": cnt_dezenas,
        "ordenados_freq": ordenados_freq,
        "quentes": quentes,
        "medias": medias,
        "frias": frias,
        "min_soma": min_soma,
        "max_soma": max_soma,
        "media_soma": media_soma,
        "max_consec": max_consec,
        "min_rep": min_rep,
        "max_rep": max_rep,
        "stats_grupos": stats_grupos
    }

# ==============================================================================
# 4. INICIALIZAÇÃO E CALIBRAÇÃO DE ESTADO
# ==============================================================================
if "grupos_base" not in st.session_state:
    st.session_state.grupos_base = construir_todos_grupos()

if "historico_sorteios" not in st.session_state:
    st.session_state.historico_sorteios = [list(j) for j in HISTORICO_30_QUINA]

# Calcula estatísticas reais com base nos 30 sorteios
stats = processar_estatisticas_completas(st.session_state.historico_sorteios, st.session_state.grupos_base)

def aplicar_calibragem_historica():
    st.session_state.filtro_soma_ativo = True
    st.session_state.faixa_soma = (int(stats["min_soma"]), int(stats["max_soma"]))
    st.session_state.filtro_consec_ativo = True
    st.session_state.max_consec = int(stats["max_consec"])
    st.session_state.f_rep_ant_ativo = True
    st.session_state.rep_ant_faixa = (int(stats["min_rep"]), int(stats["max_rep"]))
    st.session_state.f_max_coinc_ativo = True
    st.session_state.max_coinc_30 = 3
    st.session_state.f_freq_30_ativo = True
    st.session_state.faixa_quentes = (1, 3)
    st.session_state.faixa_frias = (0, 2)

    regras = {}
    for k, v in stats["stats_grupos"].items():
        regras[k] = {
            "ativo": False,
            "min": int(v["min"]),
            "max": int(v["max"])
        }
    # Ativa padrões clássicos fundamentais
    for padrao in ["Pares", "Primos", "Moldura"]:
        regras[padrao]["ativo"] = True
    
    st.session_state.regras_ativas = regras

if "regras_ativas" not in st.session_state:
    aplicar_calibragem_historica()

if "jogos_aleatorios" not in st.session_state: st.session_state.jogos_aleatorios = []
if "jogos_fechamento" not in st.session_state: st.session_state.jogos_fechamento = []

# ==============================================================================
# 5. VALIDAÇÃO DE APOSTAS E FECHAMENTO GULOSO
# ==============================================================================
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

def extrair_dezenas_texto(texto):
    numeros = re.findall(r'\b\d+\b', texto)
    validos = [int(n) for n in numeros if 1 <= int(n) <= 80]
    return sorted(list(set(validos)))

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
# 6. INTERFACE PRINCIPAL
# ==============================================================================
st.title("🎯 Quina: Laboratório & Fechamentos")
st.caption("Matriz Oficial 8x10 • Estatísticas dos 30 Concursos • Diagonais Cilíndricas Dinâmicas.")

tab_filtros, tab_hist, tab_gerador, tab_fechamento, tab_conferir, tab_volante = st.tabs([
    "⚙️ Filtros & Estatísticas",
    "📜 30 Concursos & Diagonais",
    "🚀 Gerador de Apostas",
    "🎯 Fechamentos Matemáticos",
    "🎟️ Conferir Jogos",
    "🗺️ Volante Visual 8x10"
])

hist_sets = [set(j) for j in st.session_state.historico_sorteios]
ult_set = set(st.session_state.historico_sorteios[-1]) if st.session_state.historico_sorteios else set()

# ABA 1: FILTROS E PARÂMETROS
with tab_filtros:
    c_topo1, c_topo2 = st.columns([3, 1])
    with c_topo1:
        st.subheader("1. Calibração Estatística dos Filtros")
        st.caption("Todos os filtros abaixo estão sincronizados com as ocorrências reais dos últimos 30 sorteios.")
    with c_topo2:
        if st.button("🔄 Recalibrar pelos 30 Sorteios", use_container_width=True):
            aplicar_calibragem_historica()
            st.success("Filtros sincronizados com sucesso!")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.filtro_soma_ativo = st.checkbox("Filtrar por Soma das 5 Dezenas", value=st.session_state.filtro_soma_ativo)
        st.caption(f"📊 Histórico 30: Mín = {stats['min_soma']} | Máx = {stats['max_soma']} | Média = {stats['media_soma']:.1f}")
        if st.session_state.filtro_soma_ativo:
            st.session_state.faixa_soma = st.slider("Intervalo de Soma:", 15, 390, st.session_state.faixa_soma)
    with c2:
        st.session_state.filtro_consec_ativo = st.checkbox("Limitar Números Consecutivos", value=st.session_state.filtro_consec_ativo)
        st.caption(f"📊 Histórico 30: O maior consecutivo observado em um mesmo sorteio foi **{stats['max_consec']}**")
        if st.session_state.filtro_consec_ativo:
            st.session_state.max_consec = st.slider("Máximo consecutivo permitido:", 1, 3, st.session_state.max_consec)

    st.divider()
    st.subheader("2. Restrições Baseadas nos Últimos 30 Concursos")
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.session_state.f_rep_ant_ativo = st.checkbox("Repetição do Último Concurso", value=st.session_state.f_rep_ant_ativo)
        st.caption(f"📊 Faixa nos 30: {stats['min_rep']} a {stats['max_rep']} dezenas repetidas")
        if st.session_state.f_rep_ant_ativo:
            st.session_state.rep_ant_faixa = st.slider("Dezenas repetidas:", 0, 5, st.session_state.rep_ant_faixa)
            st.caption(f"Último sorteio: `{sorted(list(ult_set))}`")
    with ch2:
        st.session_state.f_max_coinc_ativo = st.checkbox("Teto de Coincidência Histórica", value=st.session_state.f_max_coinc_ativo)
        st.caption("Evita repetir jogos com mais de 3 acertos em relação aos 30 concursos passados.")
        if st.session_state.f_max_coinc_ativo:
            st.session_state.max_coinc_30 = st.slider("Máx. acertos repetidos:", 2, 4, st.session_state.max_coinc_30)
    with ch3:
        st.session_state.f_freq_30_ativo = st.checkbox("Equilíbrio Quentes / Frias", value=st.session_state.f_freq_30_ativo)
        st.caption("Distribuição equilibrada entre as mais frequentes e atrasadas.")
        if st.session_state.f_freq_30_ativo:
            st.session_state.faixa_quentes = st.slider("Top Quentes:", 0, 5, st.session_state.faixa_quentes)
            st.session_state.faixa_frias = st.slider("Mais Atrasadas (Frias):", 0, 5, st.session_state.faixa_frias)

    st.divider()
    st.subheader("3. Padrões Clássicos da Matriz (Pares, Primos, Moldura, Miolo)")
    for padrao in ["Pares", "Primos", "Moldura", "Centro (Miolo)"]:
        s_g = stats["stats_grupos"][padrao]
        col_chk, col_sl = st.columns([2, 3])
        with col_chk:
            st.session_state.regras_ativas[padrao]["ativo"] = st.checkbox(
                f"{padrao} (Obs: Min {s_g['min']} | Máx {s_g['max']} | Média {s_g['media']:.1f})",
                value=st.session_state.regras_ativas[padrao]["ativo"],
                key=f"c_{padrao}"
            )
        with col_sl:
            if st.session_state.regras_ativas[padrao]["ativo"]:
                v = st.slider(f"Faixa {padrao}", 0, 5, (int(st.session_state.regras_ativas[padrao]["min"]), int(st.session_state.regras_ativas[padrao]["max"])), key=f"s_{padrao}")
                st.session_state.regras_ativas[padrao]["min"], st.session_state.regras_ativas[padrao]["max"] = v

    st.divider()
    st.subheader("4. Diagonais Cilíndricas (8x10) Calibradas pelo Histórico")
    st.write("Abaixo estão as 10 Diagonais Direitas e 10 Diagonais Esquerdas com estatísticas calculadas nos 30 sorteios:")
    
    col_btn_diag1, col_btn_diag2 = st.columns(2)
    with col_btn_diag1:
        if st.button("⚡ Ativar Todas as 20 Diagonais com Base no Histórico", use_container_width=True):
            for i in range(1, 11):
                st.session_state.regras_ativas[f"Diag Direita {i:02d}"]["ativo"] = True
                st.session_state.regras_ativas[f"Diag Esquerda {i:02d}"]["ativo"] = True
            st.rerun()
    with col_btn_diag2:
        if st.button("🚫 Desativar Todas as Diagonais", use_container_width=True):
            for i in range(1, 11):
                st.session_state.regras_ativas[f"Diag Direita {i:02d}"]["ativo"] = False
                st.session_state.regras_ativas[f"Diag Esquerda {i:02d}"]["ativo"] = False
            st.rerun()

    diag_dir = [f"Diag Direita {i:02d}" for i in range(1, 11)]
    diag_esq = [f"Diag Esquerda {i:02d}" for i in range(1, 11)]

    with st.expander("↘️ 10 Diagonais Direitas (Estatísticas & Filtros)"):
        for k in diag_dir:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                rotulo = f"**{k}** — Saídas: {s_d['total_saidas']}x (Média: {s_d['media']:.2f} | Min: {s_d['min']} | Máx: {s_d['max']})"
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(rotulo, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

    with st.expander("↙️ 10 Diagonais Esquerdas (Estatísticas & Filtros)"):
        for k in diag_esq:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                rotulo = f"**{k}** — Saídas: {s_d['total_saidas']}x (Média: {s_d['media']:.2f} | Min: {s_d['min']} | Máx: {s_d['max']})"
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(rotulo, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

# ABA 2: HISTÓRICO E ESTATÍSTICA DAS DIAGONAIS
with tab_hist:
    st.subheader("📜 Base Atual: 30 Últimos Concursos")
    col_hist1, col_hist2 = st.columns([3, 2])
    with col_hist1:
        dados_tabela = [
            {"Concurso": f"#{30-idx:02d}", "Dezenas": " - ".join([f"{n:02d}" for n in s]), "Soma": sum(s)}
            for idx, s in enumerate(reversed(st.session_state.historico_sorteios))
        ]
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, height=450)
    with col_hist2:
        st.markdown("#### Ranking de Dezenas (Últimos 30):")
        top_10 = [(d, stats["cnt_dezenas"][d]) for d in stats["ordenados_freq"][:10]]
        st.write("**Top 10 Quentes:** " + ", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in top_10]))
        bot_10 = sorted(stats["cnt_dezenas"].items(), key=lambda x: x[1])[:10]
        st.write("**Top 10 Frias:** " + ", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in bot_10]))

    st.divider()
    st.subheader("📊 Raio-X Estatístico das 20 Diagonais Cilíndricas (8x10)")
    dados_diags = []
    for k in (diag_dir + diag_esq):
        info = stats["stats_grupos"][k]
        dados_diags.append({
            "Diagonal": k,
            "Total Saídas": info["total_saidas"],
            "Média por Concurso": f"{info['media']:.2f}",
            "Mínimo Ocorrido": info["min"],
            "Máximo Ocorrido": info["max"],
            "Dezenas Componentes": " ".join([f"{n:02d}" for n in info["dezenas"]]),
            "Filtro Ativo?": "✅ Sim" if st.session_state.regras_ativas[k]["ativo"] else "❌ Não"
        })
    df_diags = pd.DataFrame(dados_diags).sort_values(by="Total Saídas", ascending=False)
    st.dataframe(df_diags, use_container_width=True, height=450)

# ABA 3: GERADOR
with tab_gerador:
    st.subheader("Gerar Combinações Validadas (5 Dezenas)")
    qtd = st.number_input("Quantidade de Jogos Desejada:", min_value=1, max_value=200, value=5)
    
    if st.button("Gerar Apostas da Quina 🚀", use_container_width=True):
        regras_comp = [(frozenset(st.session_state.grupos_base[k]), v["min"], v["max"]) for k, v in st.session_state.regras_ativas.items() if v["ativo"]]
        jogos, unicos, t = [], set(), 0
        pool = list(range(1, 81))
        
        with st.spinner("Filtrando combinações segundo as restrições estatísticas..."):
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
                                    stats["quentes"], stats["frias"]):
                        jogos.append(c)
                        unicos.add(ctup)
                t += 1
                
        st.session_state.jogos_aleatorios = jogos
        if not jogos:
            st.error("Nenhum jogo cumpriu todos os critérios com 250.000 iterações. Tente afrouxar algumas restrições na Aba 1.")

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
    st.subheader("🎯 Fechamentos Matemáticos Inteligentes (7 a 20 Dezenas)")
    st.caption("O sistema seleciona automaticamente por padrão as dezenas **mais sorteadas nos últimos 30 concursos**. Você pode alterá-las livremente.")
    
    sugestao_top10 = stats["ordenados_freq"][:10]
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        dezs = st.multiselect(
            "Selecione de 7 a 20 dezenas base:", 
            options=list(range(1, 81)), 
            default=sugestao_top10, 
            format_func=lambda x: f"{x:02d} (saiu {stats['cnt_dezenas'][x]}x)"
        )
    with col_f2:
        gar = st.selectbox("Garantia Matemática:", ["Quadra (Garante 4 se 5)", "Terno (Garante 3 se 5)"])

    st.write(f"📊 Dezenas selecionadas no momento: **{len(dezs)}**")
    
    if len(dezs) < 7:
        st.warning("⚠️ Selecione pelo menos 7 dezenas para processar um fechamento.")
    elif len(dezs) > 20:
        st.error("⚠️ O limite máximo para matriz fechada é de 20 dezenas.")
    else:
        if st.button("Calcular Matriz Fechada 🧮", use_container_width=True):
            with st.spinner("Calculando cobertura combinatória ótima..."):
                j_fech, cob = gerar_fechamento_guloso(dezs, gar)
                st.session_state.jogos_fechamento = j_fech
                st.session_state.taxa_cobertura = cob

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

# ABA 5: CONFERIR JOGOS
with tab_conferir:
    st.subheader("🎟️ Conferência Oficial de Apostas")
    st.write("Digite ou selecione as 5 dezenas do sorteio para calcular os prémios obtidos.")
    
    col_input1, col_input2 = st.columns([1, 1])
    with col_input1:
        res_digitado = st.text_input("Digite o resultado (ex: 05 18 32 54 76):", placeholder="05 18 32 54 76")
    with col_input2:
        res_selecionado = st.multiselect(
            "Ou selecione as 5 dezenas sorteadas:", 
            options=list(range(1, 81)), 
            max_selections=5,
            format_func=lambda x: f"{x:02d}"
        )
    
    resultado_oficial = extrair_dezenas_texto(res_digitado) if res_digitado.strip() else sorted(res_selecionado)
    
    st.divider()
    st.markdown("#### Selecione quais jogos quer conferir:")
    origem_jogos = st.radio(
        "Origem das apostas:",
        ["Jogos do Gerador (Aba 🚀)", "Jogos do Fechamento (Aba 🎯)", "Digitar / Colar outras apostas"],
        horizontal=True
    )
    
    jogos_a_testar = []
    if "Gerador" in origem_jogos:
        jogos_a_testar = st.session_state.jogos_aleatorios
        if not jogos_a_testar:
            st.info("Ainda não gerou nenhum jogo na Aba '🚀 Gerador de Apostas'.")
    elif "Fechamento" in origem_jogos:
        jogos_a_testar = st.session_state.jogos_fechamento
        if not jogos_a_testar:
            st.info("Ainda não gerou nenhum fechamento na Aba '🎯 Fechamentos Matemáticos'.")
    else:
        apostas_coladas = st.text_area(
            "Cole os seus jogos (1 jogo por linha, ex: 05 18 32 54 76):",
            placeholder="05 18 32 54 76\n01 10 25 44 70"
        )
        if apostas_coladas.strip():
            for linha in apostas_coladas.strip().split("\n"):
                nums_l = extrair_dezenas_texto(linha)
                if len(nums_l) == 5:
                    jogos_a_testar.append(nums_l)

    if len(resultado_oficial) == 5 and jogos_a_testar:
        if st.button("Conferir Todos os Bilhetes 🔍", use_container_width=True):
            set_res = set(resultado_oficial)
            contadores = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0}
            detalhes = []
            
            for j in jogos_a_testar:
                acertos = sorted(list(set(j) & set_res))
                qtd = len(acertos)
                contadores[qtd] += 1
                detalhes.append((j, acertos, qtd))
            
            st.markdown(f"### Resultado Oficial: `{' - '.join([f'{n:02d}' for n in resultado_oficial])}`")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏆 QUINA (5)", contadores[5])
            m2.metric("🎯 QUADRA (4)", contadores[4])
            m3.metric("🥈 TERNO (3)", contadores[3])
            m4.metric("🥉 DUQUE (2)", contadores[2])
            
            st.divider()
            st.markdown("#### Detalhe dos Bilhetes Conferidos:")
            
            for idx, (jogo, acertos, qtd) in enumerate(detalhes):
                premio_badge = ""
                if qtd == 5: premio_badge = "🏆 **QU
