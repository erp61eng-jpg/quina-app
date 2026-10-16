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
    [8, 25, 42, 57, 74], [14, 28, 45, 60, 76], [6, 17, 39, 53, 71],
    [10, 34, 50, 65, 77], [3, 26, 38, 51, 67], [15, 31, 43, 58, 79],
    [7, 23, 40, 56, 73], [12, 29, 46, 62, 70], [1, 18, 44, 61, 78],
    [5, 20, 37, 54, 75], [9, 24, 41, 59, 72], [16, 32, 48, 66, 80],
    [4, 21, 35, 52, 69], [13, 30, 47, 60, 76], [8, 22, 39, 57, 74],
    [11, 27, 45, 63, 77], [2, 19, 36, 50, 68], [14, 25, 42, 58, 73],
    [6, 28, 38, 55, 71], [17, 33, 49, 64, 79],
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
# 2. MAPEAMENTO DA MATRIZ 8x10
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
# 3. MOTOR ESTATÍSTICO & FUNIL DE ONDAS DE ELLIOTT
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

def calcular_funil_elliott(historico_fatia):
    """
    Sistema de Funil com base nas Ondas de Elliott:
    - Identifica a aceleração da onda (Momentum = Freq recente - Freq passada)
    - Bonifica o ponto de retração de Fibonacci no atraso (1, 2, 3, 5 concursos)
    - Penaliza dezenas em topo de onda / saturação (exaustão estatística)
    """
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
        
        # Cálculo de Atraso Atual
        atraso = 0
        for s in reversed(historico_fatia):
            if num in s:
                break
            atraso += 1

        # 1. Onda Impulsiva (Momentum de Aceleração)
        momentum = f_rec - f_ant
        pts_momentum = momentum * 2.5

        # 2. Ponto de Reversão / Retomada Fibonacci no Atraso (1, 2, 3, 5)
        pts_fibonacci = 0.0
        if atraso in [1, 2]:
            pts_fibonacci = 4.0   # Alta probabilidade de repetição/continuidade
        elif atraso in [3, 4, 5]:
            pts_fibonacci = 3.0   # Janela de quebra de ciclo
        elif atraso in [6, 7, 8]:
            pts_fibonacci = 1.5
        elif atraso > 15:
            pts_fibonacci = -3.0  # Em hibernação / fora da onda ativa

        # 3. Penalidade por Exaustão (Topo de Onda 5)
        pts_exaustao = 0.0
        if f_rec >= 4 and len(jogos_recentes) <= 10:
            pts_exaustao = -3.5  # Saturação crítica

        # Score Composto do Funil
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

    # Ordena pelo Score do Funil
    dezenas_ordenadas = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    top_20_elliott = sorted(dezenas_ordenadas[:20])
    
    return top_20_elliott, sorted(detalhes_funil, key=lambda x: x["score"], reverse=True)

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
if "jogos_fechamento_filtrados" not in st.session_state: st.session_state.jogos_fechamento_filtrados = []

# ==============================================================================
# 5. BARRA LATERAL: CONTROLE DINÂMICO
# ==============================================================================
with st.sidebar:
    st.header("Janela Estatística")
    total_disponivel = len(st.session_state.historico_sorteios)
    
    qtd_analise = st.slider(
        "Quantidade de Concursos:",
        min_value=5,
        max_value=total_disponivel,
        value=min(30, total_disponivel),
        step=1
    )
    st.caption(f"Analisando os últimos {qtd_analise} sorteios.")
    auto_sinc = st.checkbox("Sincronizar Filtros Automaticamente", value=True)

    with st.expander("Inserir Concurso Manual"):
        novo_jogo_txt = st.text_input("5 Dezenas (ex: 04 15 28 55 70):")
        if st.button("Gravar Concurso"):
            nums = [int(n) for n in re.findall(r'\b\d+\b', novo_jogo_txt) if 1 <= int(n) <= 80]
            if len(nums) == 5:
                st.session_state.historico_sorteios.append(sorted(nums))
                st.success("Concurso salvo!")
                st.rerun()
            else:
                st.error("Digite exatamente 5 números entre 1 e 80.")

historico_ativo = st.session_state.historico_sorteios[-qtd_analise:]
stats = calcular_estatisticas_dinamicas(historico_ativo, st.session_state.grupos_base)
top20_elliott, lista_funil_detalhada = calcular_funil_elliott(historico_ativo)

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
# 6. COMBINATÓRIA E UTILITÁRIOS
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
    nums = sorted(dezenas)
    if "Quina" in garantia:
        escolhidos = [sorted(list(c)) for c in combinations(nums, 5)]
        return escolhidos, 100.0

    k_alvo = 3 if "Terno" in garantia else 4
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
                if len(cands) == 6 and cands[0] < 50:
                    jogos.append(sorted(cands[1:6]))
                else:
                    jogos.append(sorted(cands[:5]))
    return jogos

def renderizar_volante_8x10(jogo, titulo=""):
    marcadas = set(jogo)
    grid_html = f"""
    <style>
        .volante-box {{ background:#ffffff; border:2px solid #2e7d32; border-radius:10px; padding:14px; width:fit-content; margin:8px auto; }}
        .volante-grid {{ display:grid; grid-template-columns:repeat(10, 36px); gap:5px; }}
        .v-cell {{ width:36px; height:36px; border:1px solid #dcdcdc; border-radius:6px; display:flex; align-items:center; justify-content:center; font-family:monospace; font-size:12px; color:#555; background:#fafafa; font-weight:500; }}
        .v-marcada {{ background:linear-gradient(135deg, #1b5e20, #2e7d32) !important; color:#ffffff !important; border:2px solid #0b4317 !important; font-weight:bold; }}
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
st.caption(f"Análise Ativa: Últimos {qtd_analise} Concursos • Sistema de Funil (Ondas de Elliott).")

tab_fechamento, tab_gerador, tab_conferir, tab_filtros, tab_hist, tab_volante = st.tabs([
    "🎯 Fechamentos & Funil de Elliott",
    "🚀 Gerador de Apostas",
    "🎟️ Conferir Jogos (TXT)",
    "⚙️ Filtros & Estatísticas",
    f"📜 Concursos ({qtd_analise}) & Diagonais",
    "🗺️ Volante Visual 8x10"
])

hist_sets = [set(j) for j in historico_ativo]
ult_set = set(historico_ativo[-1]) if historico_ativo else set()
diag_dir = [f"Diag Direita {i:02d}" for i in range(1, 11)]
diag_esq = [f"Diag Esquerda {i:02d}" for i in range(1, 11)]

# ==============================================================================
# ABA: FECHAMENTO COM FUNIL DE ELLIOTT EDITÁVEL
# ==============================================================================
with tab_fechamento:
    st.subheader(f"1. Frequência Direta (Últimos {qtd_analise} Concursos)")
    st.caption("Quantidade de saídas de cada número na janela selecionada:")

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
    st.subheader("2. As 20 Dezenas Selecionadas pelo Funil de Elliott")
    st.caption("Baseadas em aceleração da onda (Momentum), ciclos de retração de Fibonacci e descarte de exaustão:")

    str_sugestao_20 = " ".join([f"{n:02d}" for n in top20_elliott])
    st.code(f"Top 20 Elliott: {str_sugestao_20}")

    with st.expander("Ver Raio-X do Funil (Pontuação das Dezenas)"):
        df_funil = pd.DataFrame(lista_funil_detalhada[:20])
        df_funil.columns = ["Dezena", "Score Funil", "Total Saídas", "Saídas Recentes", "Momentum (Onda)", "Atraso Atual"]
        st.dataframe(df_funil, use_container_width=True)

    st.divider()
    st.subheader("3. Dezenas do Fechamento (Editável)")
    st.caption("As 20 dezenas do Funil de Elliott já vêm preenchidas abaixo. Você pode apagar, trocar ou digitar qualquer outra dezena livremente (de 7 a 20 números):")

    c_fech1, c_fech2 = st.columns([3, 1])
    with c_fech1:
        entrada_manual = st.text_input(
            "Dezenas Selecionadas:",
            value=str_sugestao_20,
            help="Altere, adicione ou remova números mantendo entre 7 e 20 dezenas."
        )
    with c_fech2:
        gar = st.selectbox(
            "Garantia Matemática:",
            [
                "Quadra (Garante 4 se 5)",
                "Terno (Garante 3 se 5)",
                "Quina (Garante 5 se 5 - 100% Fechado)"
            ]
        )

    dezenas_digitadas = extrair_dezenas_texto(entrada_manual)
    st.write(f"Dezenas ativas no bilhete ({len(dezenas_digitadas)}): `{' - '.join([f'{n:02d}' for n in dezenas_digitadas])}`")

    if len(dezenas_digitadas) < 7:
        st.info("Digite pelo menos 7 dezenas para calcular o fechamento.")
    elif len(dezenas_digitadas) > 20:
        st.error(f"Você informou {len(dezenas_digitadas)} dezenas. O limite máximo permitido é 20.")
    else:
        if st.button("Calcular Desdobramento Fechado 🧮", use_container_width=True):
            with st.spinner("Processando combinações..."):
                j_fech, cob = gerar_fechamento_guloso(dezenas_digitadas, gar)
                st.session_state.jogos_fechamento = j_fech
                st.session_state.taxa_cobertura = cob
                st.session_state.jogos_fechamento_filtrados = []

    if st.session_state.jogos_fechamento:
        qtd_bruta = len(st.session_state.jogos_fechamento)
        st.success(f"Fechamento Bruto: **{qtd_bruta} jogos gerados** (Garantia: {st.session_state.get('taxa_cobertura', 100):.1f}%)")

        st.divider()
        st.subheader("4. Depuração e Redução por Filtros Ativos")
        st.caption("Passe os jogos gerados pelos filtros da aba '⚙️ Filtros & Estatísticas' para descartar combinações improváveis e baratear o jogo.")

        if st.button("Depurar e Reduzir Jogos com Filtros Ativos 🧹", use_container_width=True):
            regras_comp = [(frozenset(st.session_state.grupos_base[k]), v["min"], v["max"]) for k, v in st.session_state.regras_ativas.items() if v["ativo"]]
            jogos_depurados = []
            
            with st.spinner("Filtrando apostas..."):
                for c in st.session_state.jogos_fechamento:
                    if validar_jogo(c, set(c), regras_comp,
                                    st.session_state.filtro_soma_ativo, st.session_state.faixa_soma,
                                    st.session_state.filtro_consec_ativo, st.session_state.max_consec,
                                    st.session_state.f_rep_ant_ativo, st.session_state.rep_ant_faixa, ult_set,
                                    st.session_state.f_max_coinc_ativo, st.session_state.max_coinc_30, hist_sets,
                                    st.session_state.f_freq_30_ativo, st.session_state.faixa_quentes, st.session_state.faixa_frias,
                                    stats["quentes"], stats["frias"]):
                        jogos_depurados.append(c)

            st.session_state.jogos_fechamento_filtrados = jogos_depurados
            
            if jogos_depurados:
                qtd_dep = len(jogos_depurados)
                reducao = ((qtd_bruta - qtd_dep) / qtd_bruta) * 100
                st.success(f"🎉 Depuração Concluída! De **{qtd_bruta}** apostas brutas, restaram apenas **{qtd_dep} jogos aprovados** (Redução de **{reducao:.1f}%** no custo).")
            else:
                st.error("Nenhum jogo do fechamento passou em todos os filtros. Alivie algumas regras na aba de Filtros.")

        if st.session_state.jogos_fechamento_filtrados:
            st.write(f"### 📋 Apostas Depuradas e Aprovadas ({len(st.session_state.jogos_fechamento_filtrados)} jogos):")
            st.download_button(
                "📥 Baixar Jogos Depurados em TXT",
                data=converter_para_txt(st.session_state.jogos_fechamento_filtrados),
                file_name="fechamento_depurado.txt",
                mime="text/plain",
                use_container_width=True
            )
            for i, j in enumerate(st.session_state.jogos_fechamento_filtrados):
                st.code(f"Aposta #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])} | Soma: {sum(j)}")

        with st.expander(f"Ver lista completa do Fechamento Bruto ({qtd_bruta} apostas)"):
            st.download_button(
                "📥 Baixar Fechamento Bruto (.TXT)",
                data=converter_para_txt(st.session_state.jogos_fechamento),
                file_name="fechamento_bruto.txt",
                mime="text/plain"
            )
            for i, j in enumerate(st.session_state.jogos_fechamento):
                st.code(f"Aposta #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])}")

# ==============================================================================
# ABA: GERADOR DE APOSTAS
# ==============================================================================
with tab_gerador:
    st.subheader("Gerar Combinações Validadas")
    qtd = st.number_input("Quantidade de Jogos:", min_value=1, max_value=200, value=5)
    
    if st.button("Gerar Apostas", use_container_width=True):
        regras_comp = [(frozenset(st.session_state.grupos_base[k]), v["min"], v["max"]) for k, v in st.session_state.regras_ativas.items() if v["ativo"]]
        jogos, unicos, t = [], set(), 0
        pool = list(range(1, 81))
        
        with st.spinner("Filtrando..."):
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
            st.error("Nenhum jogo passou pelos filtros. Ajuste os limites na aba de Filtros.")

    if st.session_state.jogos_aleatorios:
        st.success(f"{len(st.session_state.jogos_aleatorios)} jogos gerados:")
        st.download_button(
            "Baixar Jogos em TXT",
            data=converter_para_txt(st.session_state.jogos_aleatorios),
            file_name="apostas_quina.txt",
            mime="text/plain",
            use_container_width=True
        )
        for i, j in enumerate(st.session_state.jogos_aleatorios):
            st.code(f"Jogo #{i+1:02d}: {'  '.join([f'{n:02d}' for n in j])} | Soma: {sum(j)}")

# ==============================================================================
# ABA: CONFERIR JOGOS (ARQUIVO .TXT)
# ==============================================================================
with tab_conferir:
    st.subheader("Conferência Oficial com Arquivo .TXT")
    
    col_res1, col_res2 = st.columns([2, 1])
    with col_res1:
        res_digitado = st.text_input("Digite as 5 dezenas sorteadas:", placeholder="Ex: 05 18 32 54 76")
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
            st.write(f"**{len(jogos_conferir)} jogos carregados do arquivo.**")
        else:
            st.error("Nenhum jogo válido de 5 dezenas encontrado no arquivo.")
    else:
        st.caption("Ou confira apostas geradas na memória desta sessão:")
        opcao_sessao = st.selectbox(
            "Usar da memória:",
            [
                "Nenhum",
                "Jogos do Fechamento Depurado (Filtrados)",
                "Jogos do Fechamento Bruto",
                "Jogos do Gerador de Apostas"
            ]
        )
        if opcao_sessao == "Jogos do Fechamento Depurado (Filtrados)":
            jogos_conferir = st.session_state.jogos_fechamento_filtrados
        elif opcao_sessao == "Jogos do Fechamento Bruto":
            jogos_conferir = st.session_state.jogos_fechamento
        elif opcao_sessao == "Jogos do Gerador de Apostas":
            jogos_conferir = st.session_state.jogos_aleatorios

    if len(dezenas_extraidas) == 5 and jogos_conferir:
        st.divider()
        so_premiados = st.checkbox("Mostrar apenas apostas com 2 ou mais acertos", value=False)
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
        m1.metric("Quina (5)", contadores[5])
        m2.metric("Quadra (4)", contadores[4])
        m3.metric("Terno (3)", contadores[3])
        m4.metric("Duque (2)", contadores[2])
        m5.metric("Sem Prêmio", contadores[0] + contadores[1])

        st.divider()
        for idx, item in enumerate(resultados_processados):
            qtd = item["qtd_acertos"]
            if so_premiados and qtd < 2:
                continue

            tag = f"{qtd} acertos"
            if qtd == 5: tag = "QUINA!"
            elif qtd == 4: tag = "QUADRA!"
            elif qtd == 3: tag = "TERNO!"
            elif qtd == 2: tag = "DUQUE!"

            jogo_str = " ".join([f"[{n:02d}]" if n in item["acertos"] else f"{n:02d}" for n in item["jogo"]])
            st.write(f"Bilhete #{idx+1:02d}: {jogo_str} — **{tag}**")

# ==============================================================================
# ABA: FILTROS & ESTATÍSTICAS
# ==============================================================================
with tab_filtros:
    st.subheader(f"Filtros Calibrados nos Últimos {qtd_analise} Concursos")
    
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.filtro_soma_ativo = st.checkbox("Filtrar Soma", value=st.session_state.filtro_soma_ativo)
        st.caption(f"Min: {stats['min_soma']} | Max: {stats['max_soma']} | Média: {stats['media_soma']:.1f}")
        if st.session_state.filtro_soma_ativo:
            st.session_state.faixa_soma = st.slider("Faixa de Soma:", 15, 390, st.session_state.faixa_soma)
    with c2:
        st.session_state.filtro_consec_ativo = st.checkbox("Limitar Consecutivos", value=st.session_state.filtro_consec_ativo)
        st.caption(f"Maior consecutivo no período: {stats['max_consec']}")
        if st.session_state.filtro_consec_ativo:
            st.session_state.max_consec = st.slider("Máximo consecutivo:", 1, 3, st.session_state.max_consec)

    st.divider()
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.session_state.f_rep_ant_ativo = st.checkbox("Repetição Anterior", value=st.session_state.f_rep_ant_ativo)
        if st.session_state.f_rep_ant_ativo:
            st.session_state.rep_ant_faixa = st.slider("Repetidas:", 0, 5, st.session_state.rep_ant_faixa)
    with ch2:
        st.session_state.f_max_coinc_ativo = st.checkbox("Teto Coincidência Histórica", value=st.session_state.f_max_coinc_ativo)
        if st.session_state.f_max_coinc_ativo:
            st.session_state.max_coinc_30 = st.slider("Máx acertos em sorteios passados:", 2, 4, st.session_state.max_coinc_30)
    with ch3:
        st.session_state.f_freq_30_ativo = st.checkbox("Equilíbrio Quentes/Frias", value=st.session_state.f_freq_30_ativo)
        if st.session_state.f_freq_30_ativo:
            st.session_state.faixa_quentes = st.slider("Top Quentes:", 0, 5, st.session_state.faixa_quentes)
            st.session_state.faixa_frias = st.slider("Mais Atrasadas:", 0, 5, st.session_state.faixa_frias)

    st.divider()
    st.write("Padrões da Matriz:")
    for padrao in ["Pares", "Primos", "Moldura", "Centro (Miolo)"]:
        s_g = stats["stats_grupos"][padrao]
        chk, sl = st.columns([2, 3])
        with chk:
            st.session_state.regras_ativas[padrao]["ativo"] = st.checkbox(
                f"{padrao} (Min: {s_g['min']} | Max: {s_g['max']})",
                value=st.session_state.regras_ativas[padrao]["ativo"],
                key=f"c_{padrao}"
            )
        with sl:
            if st.session_state.regras_ativas[padrao]["ativo"]:
                v = st.slider(f"Faixa {padrao}", 0, 5, (int(st.session_state.regras_ativas[padrao]["min"]), int(st.session_state.regras_ativas[padrao]["max"])), key=f"s_{padrao}")
                st.session_state.regras_ativas[padrao]["min"], st.session_state.regras_ativas[padrao]["max"] = v

    st.divider()
    st.write("20 Diagonais Cilíndricas:")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Ativar 20 Diagonais"):
            for i in range(1, 11):
                st.session_state.regras_ativas[f"Diag Direita {i:02d}"]["ativo"] = True
                st.session_state.regras_ativas[f"Diag Esquerda {i:02d}"]["ativo"] = True
            st.rerun()
    with c_btn2:
        if st.button("Desativar Todas as Diagonais"):
            for i in range(1, 11):
                st.session_state.regras_ativas[f"Diag Direita {i:02d}"]["ativo"] = False
                st.session_state.regras_ativas[f"Diag Esquerda {i:02d}"]["ativo"] = False
            st.rerun()

    with st.expander("10 Diagonais Direitas"):
        for k in diag_dir:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(f"{k} (Saídas: {s_d['total_saidas']})", value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

    with st.expander("10 Diagonais Esquerdas"):
        for k in diag_esq:
            s_d = stats["stats_grupos"][k]
            chk, sl = st.columns([2, 3])
            with chk:
                st.session_state.regras_ativas[k]["ativo"] = st.checkbox(f"{k} (Saídas: {s_d['total_saidas']})", value=st.session_state.regras_ativas[k]["ativo"], key=f"c_{k}")
            with sl:
                if st.session_state.regras_ativas[k]["ativo"]:
                    v = st.slider(f"Faixa {k}", 0, 5, (int(st.session_state.regras_ativas[k]["min"]), int(st.session_state.regras_ativas[k]["max"])), key=f"s_{k}", label_visibility="collapsed")
                    st.session_state.regras_ativas[k]["min"], st.session_state.regras_ativas[k]["max"] = v

# ==============================================================================
# ABA: HISTÓRICO & TABELA DE DIAGONAIS
# ==============================================================================
with tab_hist:
    st.subheader(f"Últimos {qtd_analise} Concursos Analisados")
    c_h1, c_h2 = st.columns([3, 2])
    with c_h1:
        dados_tabela = [
            {"Concurso": f"#{len(historico_ativo)-idx:02d}", "Dezenas": " - ".join([f"{n:02d}" for n in s]), "Soma": sum(s)}
            for idx, s in enumerate(reversed(historico_ativo))
        ]
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, height=400)
    with c_h2:
        top_10 = [(d, stats["cnt_dezenas"][d]) for d in stats["ordenados_freq"][:10]]
        st.write("**Top 10 Quentes:** " + ", ".join([f"{d:02d} ({qtd}x)" for d, qtd in top_10]))
        bot_10 = sorted(stats["cnt_dezenas"].items(), key=lambda x: x[1])[:10]
        st.write("**Top 10 Frias:** " + ", ".join([f"{d:02d} ({qtd}x)" for d, qtd in bot_10]))

    st.divider()
    st.subheader("Desempenho das 20 Diagonais")
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
            "Ativo": "Sim" if st.session_state.regras_ativas[k]["ativo"] else "Não"
        })
    df_diags = pd.DataFrame(dados_diags).sort_values(by="Total Saídas", ascending=False)
    st.dataframe(df_diags, use_container_width=True, height=450)

# ==============================================================================
# ABA: VOLANTE VISUAL
# ==============================================================================
with tab_volante:
    st.subheader("Visualizador da Cartela Oficial 8x10")
    opcoes_visualizacao = ["Cartela Vazia"]
    if st.session_state.jogos_fechamento_filtrados:
        opcoes_visualizacao.extend([f"Fechamento Depurado - #{i+1:02d}" for i in range(len(st.session_state.jogos_fechamento_filtrados))])
    elif st.session_state.jogos_fechamento:
        opcoes_visualizacao.extend([f"Fechamento Bruto - #{i+1:02d}" for i in range(len(st.session_state.jogos_fechamento))])
    if st.session_state.jogos_aleatorios:
        opcoes_visualizacao.extend([f"Gerador - #{i+1:02d}" for i in range(len(st.session_state.jogos_aleatorios))])

    escolha = st.selectbox("Selecione um jogo para ver na cartela:", opcoes_visualizacao)
    jogo_exibir = []
    if "Depurado" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_fechamento_filtrados[idx]
    elif "Fechamento Bruto" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_fechamento[idx]
    elif "Gerador" in escolha:
        idx = int(escolha.split("#")[1]) - 1
        jogo_exibir = st.session_state.jogos_aleatorios[idx]

    renderizar_volante_8x10(jogo_exibir, titulo=escolha)
