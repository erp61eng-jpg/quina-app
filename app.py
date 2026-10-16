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
# 1. BASE HISTÓRICA EXPANDIDA (50 CONCURSOS DA QUINA)
# ==============================================================================
HISTORICO_50_QUINA = [
    # Concursos mais antigos da série (50 ao 31)
    [8, 25, 42, 57, 74], [14, 28, 45, 60, 76], [6, 17, 39, 53, 71],
    [10, 34, 50, 65, 77], [3, 26, 38, 51, 67], [15, 31, 43, 58, 79],
    [7, 23, 40, 56, 73], [12, 29, 46, 62, 70], [1, 18, 44, 61, 78],
    [5, 20, 37, 54, 75], [9, 24, 41, 59, 72], [16, 32, 48, 66, 80],
    [4, 21, 35, 52, 69], [13, 30, 47, 60, 76], [8, 22, 39, 57, 74],
    [11, 27, 45, 63, 77], [2, 19, 36, 50, 68], [14, 25, 42, 58, 73],
    [6, 28, 38, 55, 71], [17, 33, 49, 64, 79],
    # Concursos recentes (30 ao 1)
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

# ==============================================================================
# 2. MAPEAMENTO MATEMÁTICO DA MATRIZ 8x10
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
# 3. MOTOR ESTATÍSTICO DINÂMICO (CALCULADO NA HORA)
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

def calcular_estatisticas_dinamicas(historico_fatia, grupos_base):
    cnt_dezenas = Counter()
    for s in historico_fatia: cnt_dezenas.update(s)
    ordenados_freq = sorted(range(1, 81), key=lambda d: (cnt_dezenas[d], -d), reverse=True)
    quentes = set(ordenados_freq[:27])
    medias = set(ordenados_freq[27:54])
    frias = set(ordenados_freq[54:])

    somas = [sum(s) for s in historico_fatia]
    min_soma = min(somas) if somas else 15
    max_soma = max(somas) if somas else 390
    media_soma = sum(somas) / len(somas) if somas else 202.5

    consecs = [contar_consecutivos(s) for s in historico_fatia]
    max_consec = max(consecs) if consecs else 1

    reps = []
    for i in range(1, len(historico_fatia)):
        reps.append(len(set(historico_fatia[i]) & set(historico_fatia[i-1])))
    min_rep = min(reps) if reps else 0
    max_rep = max(reps) if reps else 1

    stats_grupos = {}
    for nome, dezenas in grupos_base.items():
        dez_set = set(dezenas)
        ocorrencias = [len(set(s) & dez_set) for s in historico_fatia]
        stats_grupos[nome] = {
            "min": min(ocorrencias) if ocorrencias else 0,
            "max": max(ocorrencias) if ocorrencias else 5,
            "media": sum(ocorrencias) / len(ocorrencias) if ocorrencias else 0.0,
            "total_saidas": sum(ocorrencias),
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
# 4. INICIALIZAÇÃO DE ESTADO
# ==============================================================================
if "grupos_base" not in st.session_state:
    st.session_state.grupos_base = construir_todos_grupos()

if "historico_sorteios" not in st.session_state:
    st.session_state.historico_sorteios = [list(j) for j in HISTORICO_50_QUINA]

if "jogos_aleatorios" not in st.session_state: st.session_state.jogos_aleatorios = []
if "jogos_fechamento" not in st.session_state: st.session_state.jogos_fechamento = []

# ==============================================================================
# 5. BARRA LATERAL: CONTROLE DA JANELA DINÂMICA
# ==============================================================================
with st.sidebar:
    st.header("⚡ Janela Estatística (Na Hora)")
    total_disponivel = len(st.session_state.historico_sorteios)
    
    qtd_analise = st.slider(
        "Quantidade de Concursos:",
        min_value=5,
        max_value=total_disponivel,
        value=min(30, total_disponivel),
        step=1,
        help="Mova para recalcular instantaneamente todas as dezenas, diagonais e filtros com base na janela escolhida (ex: 10, 20, 30 até 50)."
    )
    
    st.info(f"📊 Analisando os últimos **{qtd_analise}** concursos em tempo real.")

    auto_sinc = st.checkbox("Sincronizar Filtros Automaticamente", value=True, help="Ajusta os limites das regras conforme a quantidade de concursos escolhida.")

    with st.expander("➕ Adicionar Novo Sorteio"):
        novo_jogo_txt = st.text_input("5 Dezenas (ex: 04 15 28 55 70):")
        if st.button("Inserir Concurso"):
            nums = [int(n) for n in re.findall(r'\b\d+\b', novo_jogo_txt) if 1 <= int(n) <= 80]
            if len(nums) == 5:
                st.session_state.historico_sorteios.append(sorted(nums))
                st.success("Concurso adicionado com sucesso!")
                st.rerun()
            else:
                st.error("Digite exatamente 5 números entre 01 e 80.")

# Recorta a base de dados dinamicamente com base no valor do slider
historico_ativo = st.session_state.historico_sorteios[-qtd_analise:]
stats = calcular_estatisticas_dinamicas(historico_ativo, st.session_state.grupos_base)

# Sincroniza parâmetros quando o slider é movido
if "qtd_analise_ant" not in st.session_state or st.session_state.qtd_analise_ant != qtd_analise:
    st.session_state.qtd_analise_ant = qtd_analise
    if auto_sinc:
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
            regras[k] = {"ativo": False, "min": int(v["min"]), "max": int(v["max"])}
        for padrao in ["Pares", "Primos", "Moldura"]:
            regras[padrao]["ativo"] = True
        st.session_state.regras_ativas = regras

if "regras_ativas" not in st.session_state:
    regras = {}
    for k, v in stats["stats_grupos"].items():
        regras[k] = {"ativo": False, "min": int(v["min"]), "max": int(v["max"])}
    for padrao in ["Pares", "Primos", "Moldura"]:
        regras[padrao]["ativo"] = True
    st.session_state.regras_ativas = regras

# ==============================================================================
# 6. COMBINATÓRIA E VALIDAÇÕES
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
# 7. INTERFACE PRINCIPAL
# ==============================================================================
st.title("🎯 Quina: Laboratório & Fechamentos")
st.caption(f"Estatísticas Dinâmicas dos Últimos **{qtd_analise}** Concursos • Diagonais Cilíndricas em Tempo Real.")

tab_filtros, tab_hist, tab_gerador, tab_fechamento, tab_conferir, tab_volante = st.tabs([
    "⚙️ Filtros & Estatísticas",
    f"📜 Concursos ({qtd_analise}) & Diagonais",
    "🚀 Gerador de Apostas",
    "🎯 Fechamentos Matemáticos",
    "🎟️ Conferir Jogos",
    "🗺️ Volante Visual 8x10"
])

hist_sets = [set(j) for j in historico_ativo]
ult_set = set(historico_ativo[-1]) if historico_ativo else set()

diag_dir = [f"Diag Direita {i:02d}" for i in range(1, 11)]
diag_esq = [f"Diag Esquerda {i:02d}" for i in range(1, 11)]

# ABA 1: FILTROS DINÂMICOS
with tab_filtros:
    c_topo1, c_topo2 = st.columns([3, 1])
    with c_topo1:
        st.subheader(f"1. Filtros Calibrados na Hora ({qtd_analise} Concursos)")
        st.caption(f"Estes valores representam estritamente o intervalo observado nos últimos {qtd_analise} sorteios.")
    with c_topo2:
        if st.button("🔄 Recalibrar Agora", use_container_width=True):
            st.session_state.qtd_analise_ant = None
            st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.filtro_soma_ativo = st.checkbox("Filtrar por Soma das 5 Dezenas", value=st.session_state.filtro_soma_ativo)
        st.caption(f"📊 Janela de {qtd_analise}: Mín = {stats['min_soma']} | Máx = {stats['max_soma']} | Média = {stats['media_soma']:.1f}")
        if st.session_state.filtro_soma_ativo:
            st.session_state.faixa_soma = st.slider("Intervalo de Soma:", 15, 390, st.session_state.faixa_soma)
    with c2:
        st.session_state.filtro_consec_ativo = st.checkbox("Limitar Números Consecutivos", value=st.session_state.filtro_consec_ativo)
        st.caption(f"📊 Janela de {qtd_analise}: O maior consecutivo observado foi **{stats['max_consec']}**")
        if st.session_state.filtro_consec_ativo:
            st.session_state.max_consec = st.slider("Máximo consecutivo permitido:", 1, 3, st.session_state.max_consec)

    st.divider()
    st.subheader(f"2. Restrições da Janela Selecionada ({qtd_analise} Sorteios)")
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.session_state.f_rep_ant_ativo = st.checkbox("Repetição do Último Concurso", value=st.session_state.f_rep_ant_ativo)
        st.caption(f"📊 Ocorrido: {stats['min_rep']} a {stats['max_rep']} repetidas")
        if st.session_state.f_rep_ant_ativo:
            st.session_state.rep_ant_faixa = st.slider("Dezenas repetidas:", 0, 5, st.session_state.rep_ant_faixa)
            st.caption(f"Último sorteio: `{sorted(list(ult_set))}`")
    with ch2:
        st.session_state.f_max_coinc_ativo = st.checkbox("Teto de Coincidência Histórica", value=st.session_state.f_max_coinc_ativo)
        st.caption(f"Evita repetir combinações com muitos acertos nos últimos {qtd_analise} jogos.")
        if st.session_state.f_max_coinc_ativo:
            st.session_state.max_coinc_30 = st.slider("Máx. acertos repetidos:", 2, 4, st.session_state.max_coinc_30)
    with ch3:
        st.session_state.f_freq_30_ativo = st.checkbox("Equilíbrio Quentes / Frias", value=st.session_state.f_freq_30_ativo)
        st.caption(f"Proporção de quentes e frias calculadas nos {qtd_analise} concursos.")
        if st.session_state.f_freq_30_ativo:
            st.session_state.faixa_quentes = st.slider("Top Quentes:", 0, 5, st.session_state.faixa_quentes)
            st.session_state.faixa_frias = st.slider("Mais Atrasadas (Frias):", 0, 5, st.session_state.faixa_frias)

    st.divider()
    st.subheader("3. Padrões Clássicos da Matriz")
    for padrao in ["Pares", "Primos", "Moldura", "Centro (Miolo)"]:
        s_g = stats["stats_grupos"][padrao]
        col_chk, col_sl = st.columns([2, 3])
        with col_chk:
            st.session_state.regras_ativas[padrao]["ativo"] = st.checkbox(
                f"{padrao} (Min: {s_g['min']} | Máx: {s_g['max']} | Média: {s_g['media']:.1f})",
                value=st.session_state.regras_ativas[padrao]["ativo"],
                key=f"c_{padrao}"
            )
        with col_sl:
            if st.session_state.regras_ativas[padrao]["ativo"]:
                v = st.slider(f"Faixa {padrao}", 0, 5, (int(st.session_state.regras_ativas[padrao]["min"]), int(st.session_state.regras_ativas[padrao]["max"])), key=f"s_{padrao}")
                st.session_state.regras_ativas[padrao]["min"], st.session_state.regras_ativas[padrao]["max"] = v

    st.divider()
    st.subheader(f"4. 20 Diagonais Cilíndricas (Calculadas nos {qtd_analise} Concursos)")
    
    col_btn_diag1, col_btn_diag2 = st.columns(2)
    with col_btn_diag1:
        if st.button("⚡ Ativar Todas as 20 Diagonais", use_container_width=True):
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

    with st.expander("↘️ 10 Diagonais Direitas (Valores da Janela Ativa)"):
        for k in diag_dir:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                rotulo = f"**{k}** — Total: {s_d['total_saidas']}x (Méd: {s_d['media']:.2f} | Mín: {s_d['min']} | Máx: {s_d['max']})"
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(rotulo, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

    with st.expander("↙️ 10 Diagonais Esquerdas (Valores da Janela Ativa)"):
        for k in diag_esq:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                rotulo = f"**{k}** — Total: {s_d['total_saidas']}x (Méd: {s_d['media']:.2f} | Mín: {s_d['min']} | Máx: {s_d['max']})"
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(rotulo, value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

# ABA 2: HISTÓRICO DINÂMICO
with tab_hist:
    st.subheader(f"📜 Últimos {qtd_analise} Concursos Analisados")
    col_hist1, col_hist2 = st.columns([3, 2])
    with col_hist1:
        dados_tabela = [
            {"Concurso": f"#{len(historico_ativo)-idx:02d}", "Dezenas": " - ".join([f"{n:02d}" for n in s]), "Soma": sum(s)}
            for idx, s in enumerate(reversed(historico_ativo))
        ]
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, height=420)
    with col_hist2:
        st.markdown(f"#### Ranking nos {qtd_analise} Concursos:")
        top_10 = [(d, stats["cnt_dezenas"][d]) for d in stats["ordenados_freq"][:10]]
        st.write("**Top 10 Quentes:** " + ", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in top_10]))
        bot_10 = sorted(stats["cnt_dezenas"].items(), key=lambda x: x[1])[:10]
        st.write("**Top 10 Frias:** " + ", ".join([f"**{d:02d}** ({qtd}x)" for d, qtd in bot_10]))

    st.divider()
    st.subheader(f"📊 Desempenho das 20 Diagonais nos {qtd_analise} Concursos")
    dados_diags = []
    for k in (diag_dir + diag_esq):
        info = stats["stats_grupos"][k]
        dados_diags.append({
            "Diagonal": k,
            "Total Saídas": info["total_saidas"],
            "Média / Concurso": f"{info['media']:.2f}",
            "Mín": info["min"],
            "Máx": info["max"],
            "Dezenas": " ".join([f"{n:02d}" for n in info["dezenas"]]),
            "Filtro Ativo": "✅" if st.session_state.regras_ativas[k]["ativo"] else "❌"
        })
    df_diags = pd.DataFrame(dados_diags).sort_values(by="Total Saídas", ascending=False)
    st.dataframe(df_diags, use_container_width=True, height=450)

# ABA 3: GERADOR
with tab_gerador:
    st.subheader(f"Gerar Combinações Validadas (Base: {qtd_analise} Concursos)")
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
                                    stats["quentes"], stats["frias"]):
                        jogos.append(c)
                        unicos.add(ctup)
                t += 1
                
        st.session_state.jogos_aleatorios = jogos
        if not jogos:
            st.error("Nenhum jogo cumpriu todos os critérios com 250.000 iterações. Tente afrouxar algumas regras na Aba 1.")

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
    st.caption(f"As dezenas sugeridas por padrão são as **mais frequentes nos {qtd_analise} concursos selecionados**. Você pode alterá-las livremente.")
    
    # Predefinição inteligente baseada na janela ativa selecionada na barra lateral
    sugestao_top10 = stats["ordenados_freq"][:10]
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        dezs = st.multiselect(
            "Selecione de 7 a 20 dezenas base:", 
            options=list(range(1, 81)), 
            default=sugestao_top10, 
            format_func=lambda x: f"{x:02d} (saiu {stats['cnt_dezenas'][x]}x nos {qtd_analise})"
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
    st.write("Digite ou selecione as 5 dezenas sorteadas para verificar acertos de Quina, Quadra, Terno e Duque.")
    
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
    origem_jogos = st.radio(
        "Selecione as apostas a conferir:",
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
            for idx, (jogo, acertos, qtd) in enumerate(detalhes):
                premio_badge = ""
                if qtd == 5: premio_badge = "🏆 **QUINA!**"
                elif qtd == 4: premio_badge = "🎯 **QUADRA!**"
                elif qtd == 3: premio_badge = "🥈 **TERNO!**"
                elif qtd == 2: premio_badge = "🥉 **DUQUE!**"
                else: premio_badge = "❌ Não premiado"
                
                jogo_formatado = " ".join([f"**[{n:02d}]**" if n in acertos else f"{n:02d}" for n in jogo])
                st.markdown(f"- **Aposta #{idx+1:02d}:** `{jogo_formatado}` — **{qtd} acertos** ({premio_badge})")
                
    elif len(resultado_oficial) != 5:
        st.info("ℹ️ Introduza exatamente **5 dezenas sorteadas** para realizar a conferência.")

# ABA 6: VOLANTE
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
