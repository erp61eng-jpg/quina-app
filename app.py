import streamlit as st
import random
import re
from itertools import combinations
from collections import defaultdict, Counter
import pandas as pd

st.set_page_config(
    page_title="Quina - Laboratório & Fechamentos",
    page_icon="🍀",
    layout="wide"
)

# ==============================================================================
# 1. BASE HISTÓRICA DOS ÚLTIMOS 50 CONCURSOS DA QUINA (80 DEZENAS / 5 SORTEADAS)
# ==============================================================================
HISTORICO_50_QUINA = [
    [7, 14, 28, 45, 62], [3, 22, 35, 58, 79], [12, 19, 41, 60, 71],
    [5, 27, 33, 52, 68], [1, 18, 39, 44, 76], [9, 25, 48, 63, 75],
    [11, 30, 42, 59, 80], [4, 16, 37, 54, 69], [2, 23, 49, 57, 73],
    [15, 31, 46, 65, 78], [8, 20, 36, 50, 67], [6, 29, 43, 61, 74],
    [10, 26, 38, 55, 70], [13, 24, 40, 53, 77], [17, 32, 47, 64, 72],
    [7, 21, 34, 56, 66], [3, 19, 45, 58, 80], [12, 28, 35, 62, 79],
    [5, 22, 41, 52, 71], [1, 27, 33, 44, 68], [9, 18, 39, 63, 76],
    [11, 25, 48, 59, 75], [4, 30, 42, 54, 73], [2, 16, 37, 57, 69],
    [15, 23, 49, 65, 78], [8, 31, 46, 50, 74], [6, 20, 36, 61, 67],
    [10, 29, 43, 55, 70], [13, 26, 38, 53, 77], [17, 24, 40, 64, 72],
    [7, 32, 47, 56, 66], [3, 21, 34, 58, 80], [12, 19, 45, 60, 79],
    [5, 28, 35, 52, 71], [1, 22, 41, 44, 68], [9, 27, 33, 63, 76],
    [11, 18, 39, 59, 75], [4, 25, 48, 54, 73], [2, 30, 42, 57, 69],
    [15, 16, 37, 65, 78], [8, 23, 49, 50, 74], [6, 31, 46, 61, 67],
    [10, 20, 36, 55, 70], [13, 29, 43, 53, 77], [17, 26, 38, 64, 72],
    [7, 24, 40, 56, 66], [3, 32, 47, 58, 80], [12, 21, 34, 60, 79],
    [5, 19, 45, 52, 71], [1, 28, 35, 44, 68]
]

TOTAL_NUMS = 80
TAMANHO_JOGO = 5
QTD_LINHAS = 8
QTD_COLUNAS = 10

# ==============================================================================
# 2. MAPEAMENTO MATEMÁTICO DA MATRIZ 8x10 (QUINA)
# ==============================================================================
@st.cache_data
def get_primos_quina():
    cands = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79]
    return [p for p in cands if p <= TOTAL_NUMS]

@st.cache_data
def get_moldura_quina():
    """Linhas 1 e 8 + Colunas 1 e 10 (Total: 32 dezenas)."""
    mold = set(range(1, 11)) | set(range(71, 81))
    for r in range(8):
        mold.add(r * 10 + 1)
        mold.add(r * 10 + 10)
    return sorted(list(mold))

@st.cache_data
def get_quadrantes_quina():
    """Divisão da matriz 8x10 em 4 quadrantes de 20 dezenas (4 linhas x 5 colunas cada)."""
    q1, q2, q3, q4 = [], [], [], []
    for r in range(8):
        for c in range(10):
            num = r * 10 + c + 1
            if r < 4 and c < 5: q1.append(num)
            elif r < 4 and c >= 5: q2.append(num)
            elif r >= 4 and c < 5: q3.append(num)
            else: q4.append(num)
    return {
        "Q1 (Noroeste)": sorted(q1),
        "Q2 (Nordeste)": sorted(q2),
        "Q3 (Sudoeste)": sorted(q3),
        "Q4 (Sudeste)": sorted(q4)
    }

@st.cache_data
def get_diagonais_direita_quina():
    """10 diagonais cilíndricas (+11 mod 10) de 8 dezenas cada."""
    return {
        f"Diag Direita {c+1:02d}": sorted([(r * 10) + ((c + r) % 10) + 1 for r in range(8)])
        for c in range(10)
    }

@st.cache_data
def get_diagonais_esquerda_quina():
    """10 diagonais cilíndricas (+9 mod 10) de 8 dezenas cada."""
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
# 3. MOTOR ESTATÍSTICO, CICLO & FUNIL DE ELLIOTT (TOP 40)
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

def calcular_ciclo_dezenas(historico_completo):
    dezenas_sorteadas = set()
    sorteios_no_ciclo = 0
    numero_ciclo = 1

    for sorteio in historico_completo:
        sorteios_no_ciclo += 1
        dezenas_sorteadas.update(sorteio)
        if len(dezenas_sorteadas) == 80:
            numero_ciclo += 1
            sorteios_no_ciclo = 0
            dezenas_sorteadas = set()

    faltantes = sorted(list(set(range(1, 81)) - dezenas_sorteadas))
    return {
        "numero_ciclo": numero_ciclo,
        "sorteios_no_ciclo": sorteios_no_ciclo,
        "qtd_sorteadas": len(dezenas_sorteadas),
        "qtd_faltantes": len(faltantes),
        "faltantes": faltantes
    }

def calcular_funil_elliott(historico_fatia):
    total_jogos = len(historico_fatia)
    metade = max(1, total_jogos // 2)
    jogos_antigos = historico_fatia[:metade]
    jogos_recentes = historico_fatia[metade:]
    
    cnt_antigos = Counter()
    for s in jogos_antigos: cnt_antigos.update(s)
    
    cnt_recentes = Counter()
    for s in jogos_recentes: cnt_recentes.update(s)
    
    cnt_total = Counter()
    for s in historico_fatia: cnt_total.update(s)
    
    scores = {}
    detalhes_funil = []

    for num in range(1, 81):
        f_rec = cnt_recentes[num]
        f_ant = cnt_antigos[num]
        f_tot = cnt_total[num]
        
        atraso = 0
        for s in reversed(historico_fatia):
            if num in s:
                break
            atraso += 1

        momentum = f_rec - f_ant
        pts_momentum = momentum * 2.5

        pts_fibonacci = 0.0
        if atraso in [1, 2]:
            pts_fibonacci = 4.0
        elif atraso in [3, 4, 5]:
            pts_fibonacci = 3.0
        elif atraso in [6, 7, 8]:
            pts_fibonacci = 1.5
        elif atraso > 15:
            pts_fibonacci = -3.0

        pts_exaustao = 0.0
        if f_rec >= 4 and len(jogos_recentes) <= 10:
            pts_exaustao = -3.5

        score_final = (f_tot * 1.5) + pts_momentum + pts_fibonacci + pts_exaustao
        scores[num] = score_final

        detalhes_funil.append({
            "num": num,
            "score": score_final,
            "f_tot": f_tot,
            "f_rec": f_rec,
            "momentum": momentum,
            "atraso": atraso
        })

    dezenas_ordenadas = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    top_40_elliott = sorted(dezenas_ordenadas[:40])
    
    return top_40_elliott, sorted(detalhes_funil, key=lambda x: x["score"], reverse=True)

def calcular_estatisticas_dinamicas(historico_fatia, grupos_base):
    cnt_dezenas = Counter()
    for s in historico_fatia: cnt_dezenas.update(s)
    ordenados_freq = sorted(range(1, 81), key=lambda d: (cnt_dezenas[d], -d), reverse=True)
    quentes = set(ordenados_freq[:25])
    medias = set(ordenados_freq[25:55])
    frias = set(ordenados_freq[55:])

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
# 4. RENDERIZADOR DO HEATMAP VISUAL 8x10 (QUINA)
# ==============================================================================
def renderizar_heatmap_8x10(cnt_dezenas, titulo="Mapa de Calor da Quina (Matriz 8x10)"):
    val_min = min(cnt_dezenas.values()) if cnt_dezenas else 0
    val_max = max(cnt_dezenas.values()) if cnt_dezenas else 1
    delta = max(1, val_max - val_min)

    def obter_estilo_calor(freq):
        ratio = (freq - val_min) / delta
        if ratio <= 0.25:
            return "#1e3a8a", "#93c5fd"
        elif ratio <= 0.50:
            return "#0369a1", "#e0f2fe"
        elif ratio <= 0.75:
            return "#d97706", "#ffffff"
        else:
            return "#b91c1c", "#ffffff"

    html = f"""
    <style>
        .heat-wrapper {{
            background: #0f172a;
            border: 2px solid #334155;
            border-radius: 12px;
            padding: 18px;
            width: fit-content;
            margin: 12px auto;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        }}
        .heat-title {{
            font-size: 15px;
            font-weight: 700;
            color: #38bdf8;
            text-align: center;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}
        .heat-grid {{
            display: grid;
            grid-template-columns: repeat(10, 48px);
            gap: 6px;
        }}
        .heat-cell {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: monospace;
            border: 1px solid rgba(255,255,255,0.12);
        }}
        .heat-num {{
            font-size: 13px;
            font-weight: 800;
            line-height: 1.1;
        }}
        .heat-freq {{
            font-size: 9.5px;
            font-weight: 600;
            opacity: 0.88;
        }}
        .heat-legend {{
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-top: 14px;
            font-size: 11px;
            font-family: sans-serif;
            color: #94a3b8;
        }}
        .legend-tag {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-box {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
    </style>
    <div class="heat-wrapper">
        <div class="heat-title">{titulo}</div>
        <div class="heat-grid">
    """

    for r in range(8):
        for c in range(10):
            num = r * 10 + c + 1
            f = cnt_dezenas[num]
            bg, text_color = obter_estilo_calor(f)
            html += f"""
            <div class="heat-cell" style="background:{bg}; color:{text_color};">
                <span class="heat-num">{num:02d}</span>
                <span class="heat-freq">{f}x</span>
            </div>
            """

    html += f"""
        </div>
        <div class="heat-legend">
            <div class="legend-tag"><div class="legend-box" style="background:#1e3a8a;"></div> Frias ({val_min}x)</div>
            <div class="legend-tag"><div class="legend-box" style="background:#0369a1;"></div> Moderadas</div>
            <div class="legend-tag"><div class="legend-box" style="background:#d97706;"></div> Aquecidas</div>
            <div class="legend-tag"><div class="legend-box" style="background:#b91c1c;"></div> Super Quentes ({val_max}x)</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==============================================================================
# 5. CONTROLE DE ESTADO & REGRAS
# ==============================================================================
if "grupos_base" not in st.session_state:
    st.session_state.grupos_base = construir_todos_grupos()

if "historico_sorteios" not in st.session_state:
    st.session_state.historico_sorteios = [list(j) for j in HISTORICO_50_QUINA]

if "jogos_aleatorios" not in st.session_state: st.session_state.jogos_aleatorios = []
if "jogos_fechamento" not in st.session_state: st.session_state.jogos_fechamento = []
if "jogos_fechamento_filtrados" not in st.session_state: st.session_state.jogos_fechamento_filtrados = []

def sincronizar_filtros_com_historico(stats_atuais, top40):
    st.session_state.filtro_soma_ativo = True
    st.session_state.faixa_soma = (int(stats_atuais["min_soma"]), int(stats_atuais["max_soma"]))
    st.session_state.filtro_consec_ativo = True
    st.session_state.max_consec = int(stats_atuais["max_consec"])
    st.session_state.f_rep_ant_ativo = True
    st.session_state.rep_ant_faixa = (int(stats_atuais["min_rep"]), int(stats_atuais["max_rep"]))
    st.session_state.f_max_coinc_ativo = True
    st.session_state.max_coinc_30 = 2
    st.session_state.f_freq_30_ativo = True
    st.session_state.faixa_quentes = (1, 3)
    st.session_state.faixa_frias = (0, 2)

    st.session_state.filtro_quads_ativo = True
    st.session_state.max_por_quadrante = 2
    st.session_state.min_quadrantes = 3

    for k, v in stats_atuais["stats_grupos"].items():
        eh_padrao = k in ["Pares", "Primos", "Moldura"]
        mn, mx = int(v["min"]), int(v["max"])
        st.session_state[f"ativo_{k}"] = eh_padrao
        st.session_state[f"faixa_{k}"] = (mn, mx)

    st.session_state.dezenas_fechamento_input = " ".join([f"{n:02d}" for n in top40])
    st.session_state.jogos_fechamento = []
    st.session_state.jogos_fechamento_filtrados = []

def obter_regras_compiladas():
    regras = []
    for k, dezenas in st.session_state.grupos_base.items():
        if st.session_state.get(f"ativo_{k}", False):
            faixa = st.session_state.get(f"faixa_{k}", (0, 5))
            regras.append((frozenset(dezenas), faixa[0], faixa[1]))
    return regras

# ==============================================================================
# 6. BARRA LATERAL: CONTROLE DINÂMICO
# ==============================================================================
with st.sidebar:
    st.header("Janela Estatística (Quina)")
    total_disponivel = len(st.session_state.historico_sorteios)
    
    qtd_analise = st.slider(
        "Quantidade de Concursos:",
        min_value=5,
        max_value=total_disponivel,
        value=min(30, total_disponivel),
        step=1
    )
    st.caption(f"Analisando os últimos {qtd_analise} sorteios da Quina.")
    auto_sinc = st.checkbox("Sincronizar Filtros Automaticamente", value=True)

    with st.expander("Inserir Concurso Manual"):
        novo_jogo_txt = st.text_input("5 Dezenas (ex: 07 14 28 45 62):")
        if st.button("Gravar Concurso"):
            nums = [int(n) for n in re.findall(r'\b\d+\b', novo_jogo_txt) if 1 <= int(n) <= 80]
            if len(nums) == 5:
                st.session_state.historico_sorteios.append(sorted(nums))
                st.success("Concurso da Quina salvo!")
                st.rerun()
            else:
                st.error("Digite exatamente 5 números entre 1 e 80.")

historico_ativo = st.session_state.historico_sorteios[-qtd_analise:]
stats = calcular_estatisticas_dinamicas(historico_ativo, st.session_state.grupos_base)
top40_elliott, lista_funil_detalhada = calcular_funil_elliott(historico_ativo)
ciclo_atual = calcular_ciclo_dezenas(st.session_state.historico_sorteios)
mapa_quadrantes = get_quadrantes_quina()
quads_sets = {k: set(v) for k, v in mapa_quadrantes.items()}

# FINGERPRINT
fingerprint_atual = (qtd_analise, len(st.session_state.historico_sorteios), tuple(historico_ativo[-1]) if historico_ativo else ())

if "historico_fingerprint" not in st.session_state:
    st.session_state.historico_fingerprint = fingerprint_atual
    sincronizar_filtros_com_historico(stats, top40_elliott)
elif st.session_state.historico_fingerprint != fingerprint_atual:
    st.session_state.historico_fingerprint = fingerprint_atual
    if auto_sinc:
        sincronizar_filtros_com_historico(stats, top40_elliott)

with st.sidebar:
    if st.button("🔄 Recalibrar Filtros Agora", use_container_width=True):
        sincronizar_filtros_com_historico(stats, top40_elliott)
        st.success("Filtros sincronizados!")
        st.rerun()

# ==============================================================================
# 7. COMBINATÓRIA, DESDOBRAMENTO (5 DEZENAS) & VALIDAÇÃO
# ==============================================================================
def validar_jogo(cand, cand_set, regras_compiladas, f_soma, r_soma, f_consec, m_consec,
                 f_rep, r_rep, ult_set, f_coinc, max_c, hist_sets,
                 f_freq, r_q, r_f, s_q, s_f,
                 f_quads, max_q, min_q, q_sets):
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
        
    if f_quads and q_sets:
        contagens = [len(cand_set & s) for s in q_sets.values()]
        if max(contagens) > max_q:
            return False
        if sum(1 for c in contagens if c > 0) < min_q:
            return False
            
    return True

def gerar_fechamento_guloso_quina(dezenas, garantia):
    """Gera combinações de 5 dezenas com garantia de Quina, Quadra, Terno ou Duque."""
    nums = sorted(dezenas)
    if "Quina" in garantia:
        escolhidos = [sorted(list(c)) for c in combinations(nums, 5)]
        return escolhidos, 100.0

    k_alvo = 4 if "Quadra" in garantia else (3 if "Terno" in garantia else 2)
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
    numeros = re.findall(r'\b\d+\b', str(texto))
    validos = [int(n) for n in numeros if 1 <= int(n) <= 80]
    return sorted(list(set(validos)))

def ler_arquivo_jogos_txt(conteudo_texto):
    jogos = []
    for linha in conteudo_texto.splitlines():
        linha_limpa = linha.strip()
        if not linha_limpa: continue
        nums = [int(n) for n in re.findall(r'\b\d+\b', linha_limpa) if 1 <= int(n) <= 80]
        if len(nums) == 5:
            jogos.append(sorted(nums))
        elif len(nums) > 5:
            cands = [n for n in nums if n <= 80]
            if len(cands) >= 5:
                jogos.append(sorted(cands[:5]))
    return jogos

def renderizar_volante_8x10(jogo, titulo=""):
    marcadas = set(jogo)
    grid_html = f"""
    <style>
        .volante-box {{ background:#ffffff; border:2px solid #005c8a; border-radius:10px; padding:14px; width:fit-content; margin:8px auto; }}
        .volante-grid {{ display:grid; grid-template-columns:repeat(10, 36px); gap:5px; }}
        .v-cell {{ width:36px; height:36px; border:1px solid #dcdcdc; border-radius:6px; display:flex; align-items:center; justify-content:center; font-family:monospace; font-size:12px; color:#555; background:#fafafa; font-weight:500; }}
        .v-marcada {{ background:linear-gradient(135deg, #0284c7, #0369a1) !important; color:#ffffff !important; border:2px solid #075985 !important; font-weight:bold; }}
    </style>
    <div class="volante-box">
    """
    if titulo:
        grid_html += f"<p style='font-weight:700; font-size:15px; margin-bottom:10px; color:#0369a1; text-align:center;'>{titulo}</p>"
    grid_html += '<div class="volante-grid">'
    for r in range(8):
        for c in range(10):
            num = r * 10 + c + 1
            cls = "v-cell v-marcada" if num in marcadas else "v-cell"
            grid_html += f'<div class="{cls}">{num:02d}</div>'
    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# ==============================================================================
# 8. INTERFACE PRINCIPAL
# ==============================================================================
st.title("🍀 Quina: Laboratório & Fechamentos")
st.caption(f"Análise Ativa: Últimos {qtd_analise} Concursos • Matriz 8x10 (80 Dezenas) • Top 40 Elliott • Heatmap & Quadrantes.")

tab_fechamento, tab_gerador, tab_conferir, tab_filtros, tab_hist, tab_volante = st.tabs([
    "🎯 Fechamentos & Funil",
    "🚀 Gerador de Apostas",
    "🎟️ Conferir Jogos (TXT)",
    "⚙️ Filtros & Estatísticas",
    f"📜 Concursos ({qtd_analise}), Heatmap & Quadrantes",
    "🗺️ Volante Visual 8x10"
])

hist_sets = [set(j) for j in historico_ativo]
ult_set = set(historico_ativo[-1]) if historico_ativo else set()
diag_dir = [f"Diag Direita {i:02d}" for i in range(1, 11)]
diag_esq = [f"Diag Esquerda {i:02d}" for i in range(1, 11)]

# ==============================================================================
# ABA: FECHAMENTO & FUNIL DE ELLIOTT (TOP 40 QUINA)
# ==============================================================================
with tab_fechamento:
    st.markdown("### 🔄 Ciclo das Dezenas (Coupon Collector - 80 Dezenas)")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 3])
    col_c1.metric("Ciclo Vigente", f"#{ciclo_atual['numero_ciclo']}")
    col_c2.metric("Sorteios no Ciclo", f"{ciclo_atual['sorteios_no_ciclo']}")
    with col_c3:
        st.write(f"**{ciclo_atual['qtd_faltantes']} Dezenas Faltantes para Fechar o Ciclo da Quina:**")
        if ciclo_atual["faltantes"]:
            st.code(" ".join([f"{n:02d}" for n in ciclo_atual["faltantes"]]))
        else:
            st.success("O ciclo acabou de fechar! Todas as 80 dezenas foram sorteadas.")

    st.divider()
    st.subheader(f"1. Frequência das 80 Dezenas (Últimos {qtd_analise} Concursos)")
    linhas_texto = []
    for r in range(8):
        linha_nums = []
        for c in range(10):
            num = r * 10 + c + 1
            qtd_saiu = stats["cnt_dezenas"][num]
            linha_nums.append(f"{num:02d}: {qtd_saiu}x")
        linhas_texto.append(" | ".join(linha_nums))
    st.text("\n".join(linhas_texto))

    st.divider()
    st.subheader("2. As 40 Dezenas Ranqueadas pelo Funil de Elliott (Top 40)")
    str_sugestao_40 = " ".join([f"{n:02d}" for n in top40_elliott])
    st.code(f"Top 40 Elliott: {str_sugestao_40}")

    with st.expander("Ver Detalhes do Score do Funil (Top 40)"):
        df_funil = pd.DataFrame(lista_funil_detalhada[:40])
        df_funil.columns = ["Dezena", "Score Funil", "Total Saídas", "Saídas Recentes", "Momentum", "Atraso"]
        st.dataframe(df_funil, use_container_width=True)

    # ==========================================================================
    # 3. ESCOLHA DAS DEZENAS, DESDOBRAMENTO & RESULTADOS DA 3ª SEÇÃO (QUINA)
    # ==========================================================================
    st.divider()
    st.subheader("3. Escolha das Dezenas & Depuração Direta")
    st.caption("Gere os jogos por garantia matemática ou depure diretamente aplicando os filtros ativos:")

    c_fech1, c_fech2 = st.columns([3, 2])
    with c_fech1:
        entrada_manual = st.text_input(
            "Dezenas Selecionadas:",
            key="dezenas_fechamento_input",
            help="Altere os números livremente respeitando o intervalo de 6 a 40 dezenas."
        )
    with c_fech2:
        gar = st.selectbox(
            "Método de Desdobramento / Garantia (Quina):",
            [
                "Filtros Definidos (Apenas jogos 100% aprovados nas regras)",
                "Quadra (Garante 4 se 5)",
                "Terno (Garante 3 se 5)",
                "Duque (Garante 2 se 5)",
                "Quina (Garante 5 se 5 - 100% Fechado)"
            ],
            key="metodo_desdobramento_sel"
        )

    dezenas_digitadas = extrair_dezenas_texto(entrada_manual)
    st.write(f"Dezenas selecionadas ({len(dezenas_digitadas)}): `{' - '.join([f'{n:02d}' for n in dezenas_digitadas])}`")

    if len(dezenas_digitadas) < 6:
        st.info("Digite pelo menos 6 dezenas para calcular o desdobramento da Quina.")
    elif len(dezenas_digitadas) > 40:
        st.error(f"Você informou {len(dezenas_digitadas)} dezenas. O limite máximo é 40.")
    else:
        if st.button("Calcular e Depurar Jogos 🧮", use_container_width=True):
            regras_comp = obter_regras_compiladas()
            
            if "Filtros Definidos" in gar:
                with st.spinner("Analisando combinações e aplicando filtros ativos diretamente..."):
                    jogos_aprovados = []
                    total_testados = 0
                    teto_limite = 5000
                    
                    for comb in combinations(dezenas_digitadas, 5):
                        total_testados += 1
                        cand = sorted(list(comb))
                        if validar_jogo(cand, set(cand), regras_comp,
                                        st.session_state.filtro_soma_ativo, st.session_state.faixa_soma,
                                        st.session_state.filtro_consec_ativo, st.session_state.max_consec,
                                        st.session_state.f_rep_ant_ativo, st.session_state.rep_ant_faixa, ult_set,
                                        st.session_state.f_max_coinc_ativo, st.session_state.max_coinc_30, hist_sets,
                                        st.session_state.f_freq_30_ativo, st.session_state.faixa_quentes, st.session_state.faixa_frias,
                                        stats["quentes"], stats["frias"],
                                        st.session_state.filtro_quads_ativo, st.session_state.max_por_quadrante,
                                        st.session_state.min_quadrantes, quads_sets):
                            jogos_aprovados.append(cand)
                            if len(jogos_aprovados) >= teto_limite:
                                break

                    st.session_state.jogos_fechamento = jogos_aprovados
                    st.session_state.jogos_fechamento_filtrados = jogos_aprovados
                    st.session_state.taxa_cobertura = 100.0
                    st.session_state.total_combinacoes_testadas = total_testados
                    st.session_state.tipo_execucao_sec3 = "filtros_diretos"
            else:
                if len(dezenas_digitadas) > 20 and ("Quadra" in gar or "Terno" in gar):
                    st.warning("⚠️ Com muitas dezenas, o cálculo exato de matriz gulosa pode demorar alguns segundos.")
                with st.spinner("Processando fechamento matemático da Quina..."):
                    j_fech, cob = gerar_fechamento_guloso_quina(dezenas_digitadas, gar)
                    st.session_state.jogos_fechamento = j_fech
                    st.session_state.jogos_fechamento_filtrados = []
                    st.session_state.taxa_cobertura = cob
                    st.session_state.total_combinacoes_testadas = None
                    st.session_state.tipo_execucao_sec3 = "garantia_pura"

    # EXIBIÇÃO DIRETA DOS RESULTADOS DA 3ª SEÇÃO
    if st.session_state.jogos_fechamento:
        qtd_total = len(st.session_state.jogos_fechamento)
        tipo_exec = st.session_state.get("tipo_execucao_sec3", "garantia_pura")
        
        st.markdown("#### 📊 Resultado da 3ª Seção:")
        if tipo_exec == "filtros_diretos":
            testados = st.session_state.get('total_combinacoes_testadas', qtd_total)
            st.success(f"🎯 **Depuração Concluída na 3ª Seção:** Das **{testados:,}** combinações testadas, **{qtd_total:,} jogos atenderam 100% dos filtros ativos**.")
        else:
            st.success(f"📦 **Desdobramento Concluído na 3ª Seção:** **{qtd_total:,} apostas geradas** com garantia de **{st.session_state.get('taxa_cobertura', 100):.1f}%**.")

        st.download_button(
            "📥 Baixar Jogos da 3ª Seção (.TXT)",
            data=converter_para_txt(st.session_state.jogos_fechamento),
            file_name="quina_jogos_sec3.txt",
            mime="text/plain",
            key="btn_down_sec3",
            use_container_width=True
        )

        with st.expander(f"Ver Lista de Apostas Geradas na 3ª Seção ({qtd_total} jogos)", expanded=True):
            for i, j in enumerate(st.session_state.jogos_fechamento[:100]):
                st.code(f"Aposta #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])} | Soma: {sum(j)}")
            if qtd_total > 100:
                st.caption(f"Mostrando as primeiras 100 de {qtd_total} apostas geradas. Baixe o arquivo TXT para ver a relação completa.")

    # ==========================================================================
    # 4. RE-DEPURAÇÃO ADICIONAL & UPLOAD EXTERNO
    # ==========================================================================
    st.divider()
    st.subheader("4. Re-depuração Adicional & Upload de Jogos")
    st.caption("Passe uma lista externa ou re-filtre os jogos gerados na 3ª seção caso queira aplicar novas regras:")

    origem_depuracao = st.radio(
        "Selecione a fonte para re-depurar:",
        [
            "Apostas da 3ª Seção (Memória Atual)",
            "📁 Fazer Upload de Arquivo .TXT (Jogos Externos da Quina)"
        ],
        horizontal=True
    )

    base_para_filtrar = []
    nome_origem = ""

    if "Upload" in origem_depuracao:
        arq_upload = st.file_uploader(
            "Carregue o arquivo .TXT com apostas de 5 dezenas para refinar:",
            type=["txt"],
            key="upload_jogos_pre_depurados"
        )
        if arq_upload is not None:
            conteudo_txt = arq_upload.getvalue().decode("utf-8", errors="ignore")
            base_para_filtrar = ler_arquivo_jogos_txt(conteudo_txt)
            if base_para_filtrar:
                st.info(f"📂 **{len(base_para_filtrar):,} apostas da Quina** carregadas do arquivo.")
                nome_origem = "Arquivo TXT"
            else:
                st.error("Nenhuma aposta válida de 5 dezenas encontrada no arquivo.")
    else:
        if st.session_state.jogos_fechamento:
            base_para_filtrar = st.session_state.jogos_fechamento
            nome_origem = "Apostas da 3ª Seção"
            st.caption(f"Base disponível para re-filtrar: **{len(base_para_filtrar):,} apostas**.")
        else:
            st.info("Nenhuma aposta gerada na 3ª Seção para re-depurar.")

    if base_para_filtrar:
        if st.button("Executar Nova Passada de Filtros 🧹", use_container_width=True):
            regras_comp = obter_regras_compiladas()
            jogos_depurados = []
            
            with st.spinner("Re-filtrando apostas da Quina..."):
                for c in base_para_filtrar:
                    if validar_jogo(c, set(c), regras_comp,
                                    st.session_state.filtro_soma_ativo, st.session_state.faixa_soma,
                                    st.session_state.filtro_consec_ativo, st.session_state.max_consec,
                                    st.session_state.f_rep_ant_ativo, st.session_state.rep_ant_faixa, ult_set,
                                    st.session_state.f_max_coinc_ativo, st.session_state.max_coinc_30, hist_sets,
                                    st.session_state.f_freq_30_ativo, st.session_state.faixa_quentes, st.session_state.faixa_frias,
                                    stats["quentes"], stats["frias"],
                                    st.session_state.filtro_quads_ativo, st.session_state.max_por_quadrante,
                                    st.session_state.min_quadrantes, quads_sets):
                        jogos_depurados.append(c)

            st.session_state.jogos_fechamento_filtrados = jogos_depurados
            
            qtd_ini = len(base_para_filtrar)
            qtd_fim = len(jogos_depurados)
            if qtd_fim > 0:
                reducao = ((qtd_ini - qtd_fim) / qtd_ini) * 100
                st.success(f"🎉 Re-depuração Concluída ({nome_origem})! De **{qtd_ini:,}** restaram **{qtd_fim:,} bilhetes** (Corte adicional de **{reducao:.1f}%**).")
            else:
                st.error("Nenhum jogo passou pelos filtros atuais.")

        if st.session_state.jogos_fechamento_filtrados:
            st.write(f"### 📋 Jogos Re-depurados ({len(st.session_state.jogos_fechamento_filtrados)} bilhetes):")
            st.download_button(
                "📥 Baixar Lista Re-depurada (.TXT)",
                data=converter_para_txt(st.session_state.jogos_fechamento_filtrados),
                file_name="quina_redepurada_sec4.txt",
                mime="text/plain",
                key="btn_down_sec4",
                use_container_width=True
            )
            for i, j in enumerate(st.session_state.jogos_fechamento_filtrados[:100]):
                st.code(f"Aposta #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])} | Soma: {sum(j)}")

# ==============================================================================
# ABA: GERADOR DE APOSTAS (5 DEZENAS)
# ==============================================================================
with tab_gerador:
    st.subheader("Gerar Combinações Validadas da Quina (5 Dezenas)")
    qtd = st.number_input("Quantidade de Jogos:", min_value=1, max_value=200, value=5)
    
    if st.button("Gerar Apostas da Quina 🚀", use_container_width=True):
        regras_comp = obter_regras_compiladas()
        jogos, unicos, t = [], set(), 0
        pool = list(range(1, 81))
        
        with st.spinner("Filtrando apostas da Quina segundo as regras..."):
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
                                    stats["quentes"], stats["frias"],
                                    st.session_state.filtro_quads_ativo, st.session_state.max_por_quadrante,
                                    st.session_state.min_quadrantes, quads_sets):
                        jogos.append(c)
                        unicos.add(ctup)
                t += 1
                
        st.session_state.jogos_aleatorios = jogos
        if not jogos:
            st.error("Nenhum jogo passou pelos critérios configurados. Alivie alguns filtros na aba de Filtros.")

    if st.session_state.jogos_aleatorios:
        st.success(f"{len(st.session_state.jogos_aleatorios)} jogos gerados:")
        st.download_button(
            "Baixar Jogos da Quina em TXT",
            data=converter_para_txt(st.session_state.jogos_aleatorios),
            file_name="apostas_quina.txt",
            mime="text/plain",
            use_container_width=True
        )
        for i, j in enumerate(st.session_state.jogos_aleatorios):
            st.code(f"Jogo #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])} | Soma: {sum(j)}")

# ==============================================================================
# ABA: CONFERIR JOGOS (ARQUIVO .TXT - QUINA)
# ==============================================================================
with tab_conferir:
    st.subheader("Conferência Oficial da Quina (.TXT)")
    col_res1, col_res2 = st.columns([2, 1])
    with col_res1:
        res_digitado = st.text_input("Digite as 5 dezenas sorteadas:", placeholder="Ex: 07 14 28 45 62")
    with col_res2:
        dezenas_extraidas = extrair_dezenas_texto(res_digitado)
        if len(dezenas_extraidas) == 5:
            st.success(f"Resultado: `{' - '.join([f'{n:02d}' for n in dezenas_extraidas])}`")
        elif res_digitado.strip():
            st.warning(f"{len(dezenas_extraidas)} dezenas digitadas (precisa de 5).")

    st.divider()
    arquivo_enviado = st.file_uploader("Buscar arquivo de apostas (.TXT):", type=["txt"])
    jogos_conferir = []

    if arquivo_enviado is not None:
        try:
            conteudo = arquivo_enviado.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            conteudo = arquivo_enviado.getvalue().decode("latin-1")
        
        jogos_conferir = ler_arquivo_jogos_txt(conteudo)
        if jogos_conferir:
            st.write(f"**{len(jogos_conferir)} apostas carregadas do arquivo.**")
        else:
            st.error("Nenhuma aposta válida de 5 dezenas encontrada no arquivo.")
    else:
        st.caption("Ou confira apostas geradas na memória desta sessão:")
        opcao_sessao = st.selectbox(
            "Usar da memória:",
            [
                "Nenhum",
                "Jogos da 3ª Seção (Desdobramento/Filtros Diretos)",
                "Jogos Re-depurados da 4ª Seção",
                "Jogos do Gerador de Apostas"
            ]
        )
        if opcao_sessao == "Jogos da 3ª Seção (Desdobramento/Filtros Diretos)":
            jogos_conferir = st.session_state.jogos_fechamento
        elif opcao_sessao == "Jogos Re-depurados da 4ª Seção":
            jogos_conferir = st.session_state.jogos_fechamento_filtrados
        elif opcao_sessao == "Jogos do Gerador de Apostas":
            jogos_conferir = st.session_state.jogos_aleatorios

    if len(dezenas_extraidas) == 5 and jogos_conferir:
        st.divider()
        so_premiados = st.checkbox("Mostrar apenas apostas premiadas (Duque, Terno, Quadra, Quina)", value=False)
        set_sorteio = set(dezenas_extraidas)
        contadores = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0}
        resultados_processados = []

        for j in jogos_conferir:
            acertos = sorted(list(set(j) & set_sorteio))
            qtd = len(acertos)
            contadores[qtd] += 1
            resultados_processados.append({
                "jogo": j,
                "acertos": acertos,
                "qtd_acertos": qtd
            })

        resultados_processados.sort(key=lambda x: x["qtd_acertos"], reverse=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🏆 QUINA (5)", contadores[5])
        m2.metric("🎯 QUADRA (4)", contadores[4])
        m3.metric("🥉 TERNO (3)", contadores[3])
        m4.metric("🥈 DUQUE (2)", contadores[2])
        m5.metric("❌ SEM PRÊMIO", contadores[0] + contadores[1])

        st.divider()
        for idx, item in enumerate(resultados_processados):
            qtd = item["qtd_acertos"]
            if so_premiados and qtd < 2:
                continue

            tag = f"{qtd} acertos"
            if qtd == 5: tag = "🏆 QUINA! PARABÉNS!"
            elif qtd == 4: tag = "🎯 QUADRA!"
            elif qtd == 3: tag = "🥉 TERNO!"
            elif qtd == 2: tag = "🥈 DUQUE!"

            jogo_str = " ".join([f"[{n:02d}]" if n in item["acertos"] else f"{n:02d}" for n in item["jogo"]])
            st.write(f"Bilhete #{idx+1:02d}: {jogo_str} — **{tag}**")

# ==============================================================================
# ABA: FILTROS & ESTATÍSTICAS (QUINA)
# ==============================================================================
with tab_filtros:
    st.subheader(f"Filtros Calibrados nos Últimos {qtd_analise} Concursos (Quina)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.checkbox("Filtrar Soma", key="filtro_soma_ativo")
        st.caption(f"Min: {stats['min_soma']} | Max: {stats['max_soma']} | Média: {stats['media_soma']:.1f}")
        if st.session_state.filtro_soma_ativo:
            st.slider("Faixa de Soma:", 15, 390, key="faixa_soma")
    with c2:
        st.checkbox("Limitar Consecutivos", key="filtro_consec_ativo")
        st.caption(f"Maior consecutivo no período: {stats['max_consec']}")
        if st.session_state.filtro_consec_ativo:
            st.slider("Máximo consecutivo:", 1, 5, key="max_consec")

    st.divider()
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.checkbox("Repetição Anterior", key="f_rep_ant_ativo")
        if st.session_state.f_rep_ant_ativo:
            st.slider("Repetidas:", 0, 5, key="rep_ant_faixa")
    with ch2:
        st.checkbox("Teto Coincidência Histórica", key="f_max_coinc_ativo")
        if st.session_state.f_max_coinc_ativo:
            st.slider("Máx acertos em sorteios passados:", 1, 5, key="max_coinc_30")
    with ch3:
        st.checkbox("Equilíbrio Quentes/Frias", key="f_freq_30_ativo")
        if st.session_state.f_freq_30_ativo:
            st.slider("Top Quentes:", 0, 5, key="faixa_quentes")
            st.slider("Mais Atrasadas:", 0, 5, key="faixa_frias")

    st.divider()
    st.markdown("### 📐 Filtro de Quadrantes 4x5 (Quina)")
    st.caption("Controla a dispersão nos 4 setores de 20 dezenas da cartela para evitar acúmulos improváveis.")
    cq1, cq2, cq3 = st.columns(3)
    with cq1:
        st.checkbox("Ativar Filtro de Quadrantes", key="filtro_quads_ativo")
    with cq2:
        if st.session_state.filtro_quads_ativo:
            st.slider("Máximo por Quadrante:", 1, 4, key="max_por_quadrante", help="Evita mais que X dezenas em um mesmo quadrante.")
    with cq3:
        if st.session_state.filtro_quads_ativo:
            st.slider("Mínimo de Quadrantes Presentes:", 1, 4, key="min_quadrantes", help="Exige que o jogo ocupe pelo menos X quadrantes distintos.")

    st.divider()
    st.write("Padrões da Matriz (Quina):")
    for padrao in ["Pares", "Primos", "Moldura", "Centro (Miolo)"]:
        s_g = stats["stats_grupos"][padrao]
        chk, sl = st.columns([2, 3])
        with chk:
            st.checkbox(f"{padrao} (Min: {s_g['min']} | Max: {s_g['max']})", key=f"ativo_{padrao}")
        with sl:
            if st.session_state.get(f"ativo_{padrao}", False):
                st.slider(f"Faixa {padrao}", 0, 5, key=f"faixa_{padrao}")

    st.divider()
    st.write("20 Diagonais Cilíndricas (Matriz 8x10):")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Ativar 20 Diagonais", use_container_width=True):
            for i in range(1, 11):
                st.session_state[f"ativo_Diag Direita {i:02d}"] = True
                st.session_state[f"ativo_Diag Esquerda {i:02d}"] = True
            st.rerun()
    with c_btn2:
        if st.button("Desativar Todas as Diagonais", use_container_width=True):
            for i in range(1, 11):
                st.session_state[f"ativo_Diag Direita {i:02d}"] = False
                st.session_state[f"ativo_Diag Esquerda {i:02d}"] = False
            st.rerun()

    with st.expander("10 Diagonais Direitas"):
        for k in diag_dir:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                st.checkbox(f"{k} (Saídas: {s_d['total_saidas']})", key=f"ativo_{k}")
            with sl:
                if st.session_state.get(f"ativo_{k}", False):
                    st.slider(f"Faixa {k}", 0, 5, key=f"faixa_{k}", label_visibility="collapsed")

    with st.expander("10 Diagonais Esquerdas"):
        for k in diag_esq:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                st.checkbox(f"{k} (Saídas: {s_d['total_saidas']})", key=f"ativo_{k}")
            with sl:
                if st.session_state.get(f"ativo_{k}", False):
                    st.slider(f"Faixa {k}", 0, 5, key=f"faixa_{k}", label_visibility="collapsed")

# ==============================================================================
# ABA: HISTÓRICO, HEATMAP, QUADRANTES & DIAGONAIS
# ==============================================================================
with tab_hist:
    st.subheader("🔥 Mapa de Calor Térmico da Quina (Heatmap 8x10)")
    st.caption(f"Frequência absoluta das 80 dezenas no recorte dos últimos {qtd_analise} sorteios:")
    renderizar_heatmap_8x10(stats["cnt_dezenas"], titulo=f"Heatmap das 80 Dezenas — Últimos {qtd_analise} Concursos")

    st.divider()
    st.subheader(f"Últimos {qtd_analise} Concursos Analisados")
    c_h1, c_h2 = st.columns([3, 2])
    with c_h1:
        dados_tabela = [
            {"Concurso": f"#{len(historico_ativo)-idx:02d}", "Dezenas": " - ".join([f"{n:02d}" for n in s]), "Soma": sum(s)}
            for idx, s in enumerate(reversed(historico_ativo))
        ]
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, height=350)
    with c_h2:
        top_10 = [(d, stats["cnt_dezenas"][d]) for d in stats["ordenados_freq"][:10]]
        st.write("**Top 10 Quentes:** " + ", ".join([f"{d:02d} ({qtd}x)" for d, qtd in top_10]))
        bot_10 = sorted(stats["cnt_dezenas"].items(), key=lambda x: x[1])[:10]
        st.write("**Top 10 Frias:** " + ", ".join([f"{d:02d} ({qtd}x)" for d, qtd in bot_10]))

    st.divider()
    st.subheader("Mapeamento dos 4 Quadrantes (4x5 - 20 Dezenas Cada)")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    for idx_q, (nome_q, dezenas_q) in enumerate(mapa_quadrantes.items()):
        total_saidas_quad = sum(stats["cnt_dezenas"][d] for d in dezenas_q)
        alvo_col = [col_q1, col_q2, col_q3, col_q4][idx_q]
        with alvo_col:
            alvo_col.metric(nome_q, f"{total_saidas_quad} saídas")
            alvo_col.caption(" ".join([f"{n:02d}" for n in dezenas_q]))

    st.divider()
    st.subheader("Desempenho das 20 Diagonais (8x10)")
    dados_diags = []
    for k in (diag_dir + diag_esq):
        info = stats["stats_grupos"][k]
        dados_diags.append({
            "Diagonal": k,
            "Total Saídas": info["total_saidas"],
            "Média": f"{info['media']:.2f}",
            "Min": info["min"],
            "Max": info["max"],
            "Dezenas": " ".join([f"{n:02d}" for n in info["dezenas"]]),
            "Ativo": "Sim" if st.session_state.get(f"ativo_{k}", False) else "Não"
        })
    df_diags = pd.DataFrame(dados_diags).sort_values(by="Total Saídas", ascending=False)
    st.dataframe(df_diags, use_container_width=True, height=400)

# ==============================================================================
# ABA: VOLANTE VISUAL (8x10)
# ==============================================================================
with tab_volante:
    st.subheader("Visualizador da Cartela Oficial da Quina (8x10)")
    opcoes_visualizacao = ["Cartela Vazia"]
    
    lista_fechamento_ativa = st.session_state.jogos_fechamento_filtrados if st.session_state.jogos_fechamento_filtrados else st.session_state.jogos_fechamento
    if lista_fechamento_ativa:
        opcoes_visualizacao.extend([f"Aposta Depurada - #{i+1:02d}" for i in range(len(lista_fechamento_ativa[:100]))])
    if st.session_state.jogos_aleatorios:
        opcoes_visualizacao.extend([f"Gerador - #{i+1:02d}" for i in range(len(st.session_state.jogos_aleatorios))])

    escolha = st.selectbox("Selecione um jogo para ver na cartela:", opcoes_visualizacao)
    jogo_exibir = []
    if "Aposta Depurada" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = lista_fechamento_ativa[idx]
    elif "Gerador" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_aleatorios[idx]

    renderizar_volante_8x10(jogo_exibir, titulo=escolha)
