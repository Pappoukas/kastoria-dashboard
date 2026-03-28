"""
Kastoria Tourism Visual Analytics — app.py
==========================================
Εκκίνηση: streamlit run app.py
Αρχεία (ίδιος φάκελος ή upload):
  • color_summary_batch.xlsx
  • TripAdvisor_Kastoria_Backup.csv
  • Καστοριά_Αξιοθέατα.csv
"""

# ── imports ───────────────────────────────────────────────────────────────────
import io
import re
import tempfile
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from wordcloud import WordCloud

warnings.filterwarnings("ignore")

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kastoria Tourism Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .kpi{background:#f0f4f8;border-radius:10px;padding:16px 18px;
       border-left:4px solid #2d4a6b;margin-bottom:8px;}
  .kpi .v{font-size:26px;font-weight:700;color:#2d4a6b;}
  .kpi .l{font-size:12px;color:#555;margin-top:2px;}
  .sec{font-size:17px;font-weight:600;color:#2d4a6b;
       border-bottom:2px solid #e0d9ce;padding-bottom:5px;margin-bottom:14px;}
  .tip{background:#eef3f8;border-left:4px solid #2d4a6b;
       padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;margin:8px 0;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

MONTH_GR = {1:"Ιαν",2:"Φεβ",3:"Μαρ",4:"Απρ",5:"Μάι",6:"Ιουν",
             7:"Ιουλ",8:"Αυγ",9:"Σεπ",10:"Οκτ",11:"Νοε",12:"Δεκ"}

TRIPTYPE_GR = {"COUPLES":"Ζευγάρια","FAMILY":"Οικογένεια","FRIENDS":"Φίλοι",
               "SOLO":"Μόνος","BUSINESS":"Επαγγελματικό","NONE":"—"}

LANG_MAP = {"el":"Ελληνικά","en":"Αγγλικά","ru":"Ρωσικά","it":"Ιταλικά",
            "nl":"Ολλανδικά","iw":"Εβραϊκά","fr":"Γαλλικά","de":"Γερμανικά",
            "ja":"Ιαπωνικά","es":"Ισπανικά"}

COLORS_R = ["#c0392b","#e67e22","#f1c40f","#27ae60","#1a5276"]

ATT_CATEGORY = {
    "Kastoria Lake":"Φυσικό",
    "Cave of Dragon (Spilia tou drakou)":"Φυσικό",
    "Fossilized Forest":"Φυσικό",
    "Panagia Mavriotissa Monastery":"Πολιτιστικό",
    "Byzantine Museum of Kastoria":"Πολιτιστικό",
    "Folklore Museum of Kastoria":"Πολιτιστικό",
    "Wax Museum  of Mavrochoriou Kastorias":"Πολιτιστικό",
    "Kastorian Byzantine Churches.":"Πολιτιστικό",
    "Church of the Panagia Koumbelidiki":"Πολιτιστικό",
    "Church of St. Taksiarkhov u Mitropolii":"Πολιτιστικό",
    "Endymatologiko Mouseio":"Πολιτιστικό",
    "Prophet Elias":"Πολιτιστικό",
    "Kastoria Aquarium":"Δραστηριότητα",
    "Kastoria Outdoors":"Δραστηριότητα",
    "Adventure Kastoria":"Δραστηριότητα",
    "Mountain Lunatics":"Δραστηριότητα",
    "Culture 8 Cultural City and Nature Guided Day Tours":"Δραστηριότητα",
    "PANIK RENTALS":"Δραστηριότητα",
}
CAT_COLOR = {"Φυσικό":"#2e86ab","Πολιτιστικό":"#a23b72","Δραστηριότητα":"#f18f01","Άλλο":"#888"}

GR_STOPWORDS = set("""α αι αλλά αν αντί από αρκετά αυτά αυτές αυτή αυτό αυτοί αυτός
αφού βέβαια για γιατί γύρω δε δεν διότι εγώ εδώ είναι εκεί εκτός εμείς ενώ
εξ επίσης έτσι εάν η ηδη θα ι ίδια ίδιο ίδιος ίσως κάθε κάπου κάπως κάτι κάτω
κατά κει κι κιόλας κοντά μα μαζί μακριά μάλλον μέσα μέχρι μη μην μια μου
μόλις μόνο μόνος να ναι ο οι όλα όλες όλη όλο όλοι όλος όμως όπου όπως ότι
ούτε παρά πια πιο που πράγμα πριν πάντα πάρα σαν σας σε στα στη στην στο
στον στους συγκεκριμένα σύ συν τα τε τελικά τη την της τι τίποτα τότε τους
υπ υπάρχει υπάρχουν υπό χωρίς ώ ωστόσο ά έ ή ί ό ύ ώ
the and for are but not you all were she was said they
with have this from one had their there been would about will
into its him your can our out other than when""".split())

NEGATIVE_KW = ["βρώμικ","ακριβ","κλειστ","αγεν","χαλασ","τουαλέτ","απογοητ",
               "πρόβλημ","άσχημ","κακ","απαράδεκτ","παράπον","ελλείψ",
               "dirty","expensive","closed","rude","broken","problem","bad","disappoint"]
POSITIVE_KW = ["όμορφ","υπέροχ","εκπληκτ","φανταστ","μαγευτ","αξίζ","συστήν",
               "απίστευτ","καταπληκτ","beautiful","amazing","wonderful",
               "fantastic","great","excellent","recommend","stunning","perfect"]

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def hex_to_rgb(h):
    h = str(h).lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (128, 128, 128)

def luminance(h):
    r, g, b = hex_to_rgb(h)
    return 0.299*r + 0.587*g + 0.114*b

def color_temp(row):
    diff = float(row.get("R mean", 128)) - float(row.get("B mean", 128))
    return "Ζεστό" if diff > 15 else ("Ψυχρό" if diff < -15 else "Ουδέτερο")

def save_upload(up):
    suf = ".xlsx" if up.name.endswith(".xlsx") else ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suf) as t:
        t.write(up.read())
        return t.name

def kpi(col, val, lbl):
    col.markdown(
        f'<div class="kpi"><div class="v">{val}</div>'
        f'<div class="l">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

def sec(title):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)

def tip(text):
    st.markdown(f'<div class="tip">💡 {text}</div>', unsafe_allow_html=True)

def word_freq(texts, extra_stop=None):
    stop = GR_STOPWORDS.copy()
    if extra_stop:
        stop.update(extra_stop)
    words = []
    for t in texts:
        if pd.isna(t):
            continue
        for w in re.findall(r"[α-ωΑ-Ωa-zA-Zά-ώ]{4,}", str(t).lower()):
            if w not in stop:
                words.append(w)
    return Counter(words)

def make_wordcloud(freq_dict):
    if not freq_dict:
        return None
    wc = WordCloud(width=700, height=280, background_color="#ffffff",
                   colormap="Blues", max_words=80).generate_from_frequencies(freq_dict)
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def sentiment(t):
    if pd.isna(t):
        return "Ουδέτερο"
    tl = str(t).lower()
    pos = sum(1 for k in POSITIVE_KW if k in tl)
    neg = sum(1 for k in NEGATIVE_KW if k in tl)
    if pos > neg:
        return "Θετικό"
    if neg > pos:
        return "Αρνητικό"
    return "Ουδέτερο"

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_color(path):
    df = pd.read_excel(path, sheet_name="Summary", header=2)
    df = df[df["Status"] == "✓ OK"].copy()
    for i, suf in enumerate(["", ".1", ".2", ".3", ".4"]):
        df[f"C{i+1}_hex"] = df.get(f"HEX{suf}", "")
        df[f"C{i+1}_pct"] = pd.to_numeric(df.get(f"%{suf}", 0), errors="coerce").fillna(0)
        df[f"C{i+1}_name"] = df.get(f"Name{suf}", "")
    df["Color_temp"] = df.apply(color_temp, axis=1)
    df["Category"] = df["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    return df

@st.cache_data(show_spinner=False)
def load_stats(path):
    df = pd.read_excel(path, sheet_name="Statistics", header=2)
    return df

@st.cache_data(show_spinner=False)
def load_reviews(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)
    df["id"]            = pd.to_numeric(df["id"], errors="coerce")
    df["publishedDate"] = pd.to_datetime(df["publishedDate"], dayfirst=True, errors="coerce")
    df["travelDate"]    = pd.to_datetime(df["travelDate"], format="%Y-%m", errors="coerce")
    df["review_len"]    = df["text"].fillna("").apply(len)
    df["has_photo"]     = df["Photocount"].fillna(0) > 0
    df["has_response"]  = df["ownerResponse/text"].notna()
    df["year"]          = df["publishedDate"].dt.year
    df["month"]         = df["publishedDate"].dt.month
    df["travelMonth"]   = df["travelDate"].dt.month
    df["lang_label"]    = df["lang"].map(LANG_MAP).fillna("Άλλη")
    df["tripType_gr"]   = df["tripType"].map(TRIPTYPE_GR).fillna("—")
    df["Category"]      = df["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    df["is_foreign"]    = df["lang"] != "el"
    df["sentiment"]     = df["text"].apply(sentiment)
    return df

@st.cache_data(show_spinner=False)
def load_attractions(path):
    df = pd.read_csv(path, encoding="utf-8-sig", sep=None, engine="python")
    df["placeInfo/latitude"]  = pd.to_numeric(
        df["placeInfo/latitude"].astype(str).str.replace(",", "."), errors="coerce")
    df["placeInfo/longitude"] = pd.to_numeric(
        df["placeInfo/longitude"].astype(str).str.replace(",", "."), errors="coerce")
    df["Category"] = df["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    return df

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — file upload & filters
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🏛️ Kastoria Analytics")
    st.caption("Χρωματική ανάλυση & κριτικές TripAdvisor")
    st.divider()

    st.markdown("### 📁 Αρχεία δεδομένων")
    up_color = st.file_uploader("Excel χρωμάτων (.xlsx)",  type=["xlsx"])
    up_rev   = st.file_uploader("CSV κριτικών (.csv)",     type=["csv"], key="rev")
    up_att   = st.file_uploader("CSV αξιοθέατων (.csv)",  type=["csv"], key="att")

    def resolve(up, default):
        if up:
            return save_upload(up)
        if Path(default).exists():
            return default
        return None

    p_color = resolve(up_color, "color_summary_batch.xlsx")
    p_rev   = resolve(up_rev,   "TripAdvisor_Kastoria_Backup.csv")
    p_att   = resolve(up_att,   "Καστοριά_Αξιοθέατα.csv")

    missing = [n for n, p in [("Excel χρωμάτων", p_color),
                                ("CSV κριτικών",  p_rev),
                                ("CSV αξιοθέατων", p_att)] if not p]
    if missing:
        st.error("Λείπουν: " + ", ".join(missing))
        st.stop()

# ── Load data ──────────────────────────────────────────────────────────────
with st.spinner("Φόρτωση δεδομένων…"):
    df_color = load_color(p_color)
    df_stats = load_stats(p_color)
    df_rev   = load_reviews(p_rev)
    df_att   = load_attractions(p_att)

# Main join: color ↔ reviews
REVIEW_COLS = ["id","rating","lang","lang_label","tripType","tripType_gr",
               "travelMonth","year","month","helpfulVotes","Photocount",
               "has_photo","has_response","review_len","sentiment","is_foreign",
               "user/userLocation/name","user/contributions/totalContributions"]
df_merged = df_color.merge(df_rev[REVIEW_COLS], left_on="ID", right_on="id", how="left")

# ── Sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.markdown("### 🔍 Φίλτρα")

    all_att  = sorted(df_rev["placeInfo/name"].dropna().unique())
    sel_att  = st.multiselect("Αξιοθέατα", all_att, default=all_att)

    yrs = sorted(df_rev["year"].dropna().unique().astype(int))
    yr_range = st.slider("Έτος κριτικής", int(min(yrs)), int(max(yrs)),
                         (int(min(yrs)), int(max(yrs))))

    sel_langs = st.multiselect("Γλώσσα", sorted(df_rev["lang_label"].dropna().unique()),
                                default=sorted(df_rev["lang_label"].dropna().unique()))

    all_trips = [v for v in TRIPTYPE_GR.values() if v != "—"]
    sel_trips = st.multiselect("Τύπος ταξιδιού", all_trips, default=all_trips)

rev_f = df_rev[
    df_rev["placeInfo/name"].isin(sel_att) &
    df_rev["year"].between(yr_range[0], yr_range[1]) &
    df_rev["lang_label"].isin(sel_langs) &
    (df_rev["tripType_gr"].isin(sel_trips) | (df_rev["tripType_gr"] == "—"))
]
col_f = df_merged[df_merged["placeInfo/name"].isin(sel_att)]

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════

(tab_dash, tab_pop, tab_rat, tab_text,
 tab_geo, tab_trip, tab_inter, tab_color_tab, tab_cmp) = st.tabs([
    "📊 Dashboard",
    "📈 Δημοφιλία",
    "⭐ Βαθμολογίες",
    "💬 Κείμενο & Sentiment",
    "🌍 Γλώσσα & Προέλευση",
    "👥 Τύπος Ταξιδιού",
    "📸 Αλληλεπίδραση",
    "🎨 Χρωματική Ανάλυση",
    "📐 Συγκριτικές",
])

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
with tab_dash:
    sec("Επισκόπηση δεδομένων")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpi(c1, f"{len(rev_f):,}",                               "Κριτικές")
    kpi(c2, rev_f["placeInfo/name"].nunique(),                "Αξιοθέατα")
    kpi(c3, f"{rev_f['rating'].mean():.2f}★",                 "Μέση βαθμολογία")
    kpi(c4, f"{(rev_f['rating']==5).mean()*100:.0f}%",        "5★ ποσοστό")
    kpi(c5, f"{len(col_f):,}",                               "Φωτ/φίες χρωμ/σμένες")
    kpi(c6, rev_f["lang_label"].nunique(),                    "Γλώσσες κριτικών")

    st.divider()
    cl, cr = st.columns(2)

    with cl:
        sec("Κριτικές ανά αξιοθέατο")
        d = rev_f["placeInfo/name"].value_counts().reset_index()
        d.columns = ["Αξιοθέατο","Κριτικές"]
        d["Κατηγορία"] = d["Αξιοθέατο"].map(ATT_CATEGORY).fillna("Άλλο")
        fig = px.bar(d, x="Κριτικές", y="Αξιοθέατο", orientation="h",
                     color="Κατηγορία", color_discrete_map=CAT_COLOR,
                     template="plotly_white", text="Κριτικές")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=440, yaxis_title="", legend_title="Κατηγορία")
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Μέση βαθμολογία ανά αξιοθέατο")
        d2 = rev_f.groupby("placeInfo/name")["rating"].agg(["mean","count"]).reset_index()
        d2.columns = ["Αξιοθέατο","Μέση","n"]
        d2 = d2[d2["n"]>=5].sort_values("Μέση")
        d2["Κατηγορία"] = d2["Αξιοθέατο"].map(ATT_CATEGORY).fillna("Άλλο")
        fig2 = px.bar(d2, x="Μέση", y="Αξιοθέατο", orientation="h",
                      color="Κατηγορία", color_discrete_map=CAT_COLOR,
                      template="plotly_white", text="Μέση", range_x=[3.5, 5.3])
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(height=440, yaxis_title="", legend_title="Κατηγορία")
        st.plotly_chart(fig2, use_container_width=True)

    att_map = df_att.dropna(subset=["placeInfo/latitude","placeInfo/longitude"])
    if len(att_map) > 0:
        sec("Χάρτης αξιοθέατων Καστοριάς")
        rc = rev_f["placeInfo/name"].value_counts().reset_index()
        rc.columns = ["placeInfo/name","Κριτικές"]
        map_df = att_map.merge(rc, on="placeInfo/name", how="left")
        map_df["Κριτικές"] = map_df["Κριτικές"].fillna(5)
        fig_map = px.scatter_mapbox(
            map_df, lat="placeInfo/latitude", lon="placeInfo/longitude",
            hover_name="placeInfo/name", size="Κριτικές",
            color="Category", color_discrete_map=CAT_COLOR,
            size_max=30, zoom=13, mapbox_style="open-street-map",
        )
        fig_map.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0),
                               legend_title="Κατηγορία")
        st.plotly_chart(fig_map, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΔΗΜΟΦΙΛΙΑ
# ─────────────────────────────────────────────────────────────────────────────
with tab_pop:
    sec("1. Δημοφιλία & Επισκεψιμότητα")

    cl, cr = st.columns(2)
    with cl:
        sec("Χρονική εξέλιξη κριτικών")
        monthly = rev_f.groupby(["year","month"]).size().reset_index(name="n")
        monthly["date"] = pd.to_datetime(monthly[["year","month"]].assign(day=1))
        fig = px.line(monthly.sort_values("date"), x="date", y="n",
                      template="plotly_white", labels={"date":"","n":"Κριτικές"})
        fig.update_traces(line_color="#2d4a6b", line_width=2)
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Εποχικότητα — μήνας ταξιδιού")
        seas = rev_f.groupby("travelMonth").size().reset_index(name="n").dropna()
        seas["lbl"] = seas["travelMonth"].apply(lambda m: MONTH_GR.get(int(m),""))
        fig2 = px.bar(seas, x="lbl", y="n", color="n",
                      color_continuous_scale="Blues", template="plotly_white",
                      text="n", labels={"lbl":"","n":"Κριτικές"})
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=280, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Κριτικές ανά έτος — top αξιοθέατα")
    top8 = rev_f["placeInfo/name"].value_counts().head(8).index.tolist()
    yrly = rev_f[rev_f["placeInfo/name"].isin(top8)].groupby(
        ["year","placeInfo/name"]).size().reset_index(name="n")
    fig3 = px.line(yrly, x="year", y="n", color="placeInfo/name",
                   markers=True, template="plotly_white",
                   labels={"year":"Έτος","n":"Κριτικές","placeInfo/name":"Αξιοθέατο"})
    fig3.update_layout(height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Χρόνος ζωής κριτικών ανά αξιοθέατο")
        span = rev_f.groupby("placeInfo/name")["publishedDate"].agg(["min","max"]).reset_index()
        span.columns = ["Αξιοθέατο","Πρώτη","Τελευταία"]
        span = span.dropna().sort_values("Πρώτη")
        fig4 = px.timeline(span.assign(Task=span["Αξιοθέατο"]),
                           x_start="Πρώτη", x_end="Τελευταία", y="Αξιοθέατο",
                           color="Αξιοθέατο", template="plotly_white")
        fig4.update_layout(height=380, showlegend=False, yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Heatmap κριτικών (έτος × μήνας)")
        hm = rev_f.groupby(["year","month"]).size().reset_index(name="n").dropna()
        hm["lbl"] = hm["month"].apply(lambda m: MONTH_GR.get(int(m),""))
        pivot = hm.pivot(index="year", columns="lbl", values="n").fillna(0)
        col_order = [v for v in MONTH_GR.values() if v in pivot.columns]
        pivot = pivot.reindex(columns=col_order)
        fig5 = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto",
                         text_auto=True, template="plotly_white",
                         labels=dict(x="Μήνας", y="Έτος", color="Κριτικές"))
        fig5.update_layout(height=380)
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΒΑΘΜΟΛΟΓΙΕΣ
# ─────────────────────────────────────────────────────────────────────────────
with tab_rat:
    sec("2. Ικανοποίηση & Βαθμολογίες")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή βαθμολογιών")
        rd = rev_f["rating"].value_counts().sort_index().reset_index()
        rd.columns = ["Βαθμολογία","n"]
        rd["lbl"] = rd["Βαθμολογία"].astype(str) + "★"
        fig = px.bar(rd, x="lbl", y="n", color="lbl",
                     color_discrete_sequence=COLORS_R[::-1],
                     template="plotly_white", text="n",
                     labels={"lbl":"","n":"Κριτικές"})
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, height=290)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Διαχρονική τάση βαθμολογίας")
        trend = rev_f.groupby("year")["rating"].agg(["mean","count"]).reset_index()
        trend.columns = ["Έτος","Μέση","n"]
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(x=trend["Έτος"], y=trend["n"],
                               name="Κριτικές", marker_color="#b8d4f5"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=trend["Έτος"], y=trend["Μέση"],
                                   name="Μέση βαθμ.", line=dict(color="#e07b39", width=2),
                                   mode="lines+markers"), secondary_y=True)
        fig2.update_layout(template="plotly_white", height=290,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig2.update_yaxes(title_text="Κριτικές", secondary_y=False)
        fig2.update_yaxes(title_text="Βαθμ.", range=[4.0,5.2], secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Κατανομή βαθμολογιών ανά αξιοθέατο")
    rat_att = rev_f.groupby(["placeInfo/name","rating"]).size().reset_index(name="n")
    rat_att["lbl"] = rat_att["rating"].astype(str) + "★"
    fig3 = px.bar(rat_att, x="n", y="placeInfo/name", color="lbl",
                  barmode="relative", orientation="h",
                  color_discrete_sequence=COLORS_R[::-1],
                  template="plotly_white",
                  labels={"n":"Κριτικές","placeInfo/name":"","lbl":"Βαθμολογία"})
    fig3.update_layout(height=400, yaxis_title="")
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Βαθμολογία ανά κατηγορία")
        cat_r = rev_f.groupby("Category")["rating"].agg(["mean","std"]).reset_index()
        cat_r.columns = ["Κατηγορία","Μέση","Std"]
        fig4 = px.bar(cat_r, x="Κατηγορία", y="Μέση", error_y="Std",
                      color="Κατηγορία", color_discrete_map=CAT_COLOR,
                      template="plotly_white", text="Μέση", range_y=[3.5,5.5])
        fig4.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig4.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Μήνας ταξιδιού vs Βαθμολογία")
        sm = rev_f.groupby("travelMonth")["rating"].mean().reset_index().dropna()
        sm["lbl"] = sm["travelMonth"].apply(lambda m: MONTH_GR.get(int(m),""))
        fig5 = px.bar(sm, x="lbl", y="rating", color="rating",
                      color_continuous_scale="RdYlGn", range_color=[4.0,5.0],
                      template="plotly_white", text="rating",
                      labels={"lbl":"","rating":"Μέση βαθμολογία"}, range_y=[3.8,5.2])
        fig5.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig5.update_layout(height=300, coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΚΕΙΜΕΝΟ & SENTIMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_text:
    sec("3. Ανάλυση κειμένου & Sentiment")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή sentiment")
        sd = rev_f["sentiment"].value_counts().reset_index()
        sd.columns = ["Sentiment","n"]
        fig = px.pie(sd, values="n", names="Sentiment", hole=0.45,
                     color="Sentiment",
                     color_discrete_map={"Θετικό":"#27ae60","Αρνητικό":"#c0392b","Ουδέτερο":"#888"},
                     template="plotly_white")
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Sentiment ανά αξιοθέατο")
        sa = rev_f.groupby(["placeInfo/name","sentiment"]).size().reset_index(name="n")
        fig2 = px.bar(sa, x="n", y="placeInfo/name", color="sentiment",
                      barmode="stack", orientation="h",
                      color_discrete_map={"Θετικό":"#27ae60","Αρνητικό":"#c0392b","Ουδέτερο":"#888"},
                      template="plotly_white",
                      labels={"n":"Κριτικές","placeInfo/name":"","sentiment":"Sentiment"})
        fig2.update_layout(height=360, yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    sec("Word Cloud κριτικών")
    wc1, wc2 = st.columns(2)
    with wc1:
        st.markdown("**Όλες οι κριτικές**")
        buf = make_wordcloud(dict(word_freq(rev_f["text"].tolist()).most_common(100)))
        if buf:
            st.image(buf)
    with wc2:
        st.markdown("**Αρνητικές κριτικές (1-2★)**")
        neg_t = rev_f[rev_f["rating"]<=2]["text"].tolist()
        buf2 = make_wordcloud(dict(word_freq(neg_t).most_common(100)))
        if buf2:
            st.image(buf2)
        else:
            st.info("Δεν υπάρχουν αρκετές αρνητικές κριτικές.")

    sec("Top 30 λέξεις")
    freq_df = pd.DataFrame(word_freq(rev_f["text"].tolist()).most_common(30),
                            columns=["Λέξη","Συχνότητα"])
    fig3 = px.bar(freq_df, x="Συχνότητα", y="Λέξη", orientation="h",
                  color="Συχνότητα", color_continuous_scale="Blues",
                  template="plotly_white", text="Συχνότητα")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(height=540, yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

    sec("Word Cloud ανά αξιοθέατο")
    att_wc = st.selectbox("Αξιοθέατο", rev_f["placeInfo/name"].value_counts().index.tolist(),
                           key="wc_att")
    buf3 = make_wordcloud(dict(word_freq(
        rev_f[rev_f["placeInfo/name"]==att_wc]["text"].tolist()).most_common(100)))
    if buf3:
        st.image(buf3)

# ─────────────────────────────────────────────────────────────────────────────
# ΓΛΩΣΣΑ & ΠΡΟΕΛΕΥΣΗ
# ─────────────────────────────────────────────────────────────────────────────
with tab_geo:
    sec("4. Γλωσσική & Γεωγραφική Προέλευση")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή γλωσσών")
        ld = rev_f["lang_label"].value_counts().reset_index()
        ld.columns = ["Γλώσσα","n"]
        fig = px.pie(ld, values="n", names="Γλώσσα", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     template="plotly_white")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Μέση βαθμολογία ανά γλώσσα")
        lr = rev_f.groupby("lang_label")["rating"].agg(["mean","count"]).reset_index()
        lr.columns = ["Γλώσσα","Μέση","n"]
        lr = lr[lr["n"]>=3].sort_values("Μέση")
        fig2 = px.bar(lr, x="Γλώσσα", y="Μέση",
                      color="Μέση", color_continuous_scale="RdYlGn", range_color=[4.0,5.0],
                      template="plotly_white", text="Μέση", range_y=[3.5,5.3])
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, height=300, xaxis_tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Ξενόγλωσσες κριτικές ανά αξιοθέατο (%)")
    fg = rev_f.groupby("placeInfo/name")["is_foreign"].agg(["sum","count"]).reset_index()
    fg.columns = ["Αξιοθέατο","Ξένες","Σύνολο"]
    fg["Ποσοστό %"] = (fg["Ξένες"]/fg["Σύνολο"]*100).round(1)
    fg = fg.sort_values("Ποσοστό %", ascending=False)
    fig3 = px.bar(fg, x="Ποσοστό %", y="Αξιοθέατο", orientation="h",
                  color="Ποσοστό %", color_continuous_scale="Oranges",
                  template="plotly_white", text="Ποσοστό %")
    fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig3.update_layout(height=380, yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Heatmap: γλώσσα × αξιοθέατο")
        la = rev_f.groupby(["placeInfo/name","lang_label"]).size().reset_index(name="n")
        pv = la.pivot(index="placeInfo/name", columns="lang_label", values="n").fillna(0)
        fig4 = px.imshow(pv, color_continuous_scale="Blues", aspect="auto",
                         text_auto=True, template="plotly_white",
                         labels=dict(x="Γλώσσα", y="Αξιοθέατο", color="Κριτικές"))
        fig4.update_layout(height=420)
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Top 20 πόλεις προέλευσης")
        loc = rev_f["user/userLocation/name"].value_counts().head(20).reset_index()
        loc.columns = ["Τοποθεσία","n"]
        fig5 = px.bar(loc, x="n", y="Τοποθεσία", orientation="h",
                      color="n", color_continuous_scale="Blues",
                      template="plotly_white", text="n")
        fig5.update_traces(textposition="outside")
        fig5.update_layout(height=420, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΤΥΠΟΣ ΤΑΞΙΔΙΟΥ
# ─────────────────────────────────────────────────────────────────────────────
with tab_trip:
    sec("5. Τύπος Ταξιδιού & Προτιμήσεις")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή τύπου ταξιδιού")
        td = rev_f[rev_f["tripType_gr"]!="—"]["tripType_gr"].value_counts().reset_index()
        td.columns = ["Τύπος","n"]
        fig = px.pie(td, values="n", names="Τύπος", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     template="plotly_white")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Βαθμολογία ανά τύπο ταξιδιού")
        fig2 = px.box(rev_f[rev_f["tripType_gr"]!="—"], x="tripType_gr", y="rating",
                      color="tripType_gr",
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      template="plotly_white",
                      labels={"tripType_gr":"","rating":"Βαθμολογία"})
        fig2.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Heatmap: τύπος ταξιδιού × αξιοθέατο")
    tp = rev_f[rev_f["tripType_gr"]!="—"].groupby(
        ["placeInfo/name","tripType_gr"]).size().reset_index(name="n")
    hm = tp.pivot(index="placeInfo/name", columns="tripType_gr", values="n").fillna(0)
    fig3 = px.imshow(hm, color_continuous_scale="Purples", aspect="auto",
                     text_auto=True, template="plotly_white",
                     labels=dict(x="Τύπος", y="Αξιοθέατο", color="Κριτικές"))
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    for col, trip in [(cl,"Οικογένεια"),(cr,"Ζευγάρια")]:
        with col:
            sub = rev_f[rev_f["tripType_gr"]==trip]["placeInfo/name"].value_counts().head(8).reset_index()
            sub.columns = ["Αξιοθέατο","n"]
            ft = px.bar(sub, x="n", y="Αξιοθέατο", orientation="h",
                        color="n", color_continuous_scale="Blues",
                        template="plotly_white", text="n", title=f"Top αξιοθέατα — {trip}")
            ft.update_traces(textposition="outside")
            ft.update_layout(height=300, yaxis_title="", coloraxis_showscale=False)
            st.plotly_chart(ft, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΑΛΛΗΛΕΠΙΔΡΑΣΗ
# ─────────────────────────────────────────────────────────────────────────────
with tab_inter:
    sec("6. Αλληλεπίδραση & Δραστηριότητα Χρηστών")

    cl, cr = st.columns(2)
    with cl:
        sec("Φωτογραφίες ανά βαθμολογία")
        ph = rev_f.groupby("rating")["Photocount"].mean().reset_index()
        ph.columns = ["Βαθμολογία","Μέσος αρ."]
        fig = px.bar(ph, x="Βαθμολογία", y="Μέσος αρ.",
                     color="Μέσος αρ.", color_continuous_scale="Blues",
                     template="plotly_white", text="Μέσος αρ.")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Helpful votes ανά βαθμολογία")
        hv = rev_f.groupby("rating")["helpfulVotes"].mean().reset_index()
        hv.columns = ["Βαθμολογία","Μέσα votes"]
        fig2 = px.bar(hv, x="Βαθμολογία", y="Μέσα votes",
                      color="Μέσα votes", color_continuous_scale="Greens",
                      template="plotly_white", text="Μέσα votes")
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, height=280)
        st.plotly_chart(fig2, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Απαντήσεις διαχειριστών (%)")
        rsp = rev_f.groupby("placeInfo/name")["has_response"].agg(["sum","count"]).reset_index()
        rsp.columns = ["Αξιοθέατο","Απαντ.","Σύνολο"]
        rsp["Ποσοστό %"] = (rsp["Απαντ."]/rsp["Σύνολο"]*100).round(1)
        rsp = rsp[rsp["Σύνολο"]>=5].sort_values("Ποσοστό %", ascending=False)
        fig3 = px.bar(rsp, x="Ποσοστό %", y="Αξιοθέατο", orientation="h",
                      color="Ποσοστό %", color_continuous_scale="Teal",
                      template="plotly_white", text="Ποσοστό %")
        fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig3.update_layout(height=340, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with cr:
        sec("Μέγεθος κριτικής vs Βαθμολογία")
        rl = rev_f[rev_f["review_len"]<3000].copy()
        rl["lbl"] = rl["rating"].astype(str) + "★"
        fig4 = px.box(rl, x="lbl", y="review_len",
                      color="lbl", color_discrete_sequence=COLORS_R[::-1],
                      template="plotly_white",
                      labels={"review_len":"Χαρακτήρες","lbl":""})
        fig4.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig4, use_container_width=True)

    sec("Με/χωρίς φωτογραφία ανά βαθμολογία")
    ph2 = rev_f.groupby(["rating","has_photo"]).size().reset_index(name="n")
    ph2["Φωτ."] = ph2["has_photo"].map({True:"Με φωτ.",False:"Χωρίς φωτ."})
    fig5 = px.bar(ph2, x="rating", y="n", color="Φωτ.", barmode="group",
                  template="plotly_white",
                  color_discrete_map={"Με φωτ.":"#2d4a6b","Χωρίς φωτ.":"#b8d4f5"},
                  labels={"rating":"Βαθμολογία","n":"Κριτικές"})
    fig5.update_layout(height=280)
    st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΧΡΩΜΑΤΙΚΗ ΑΝΑΛΥΣΗ
# ─────────────────────────────────────────────────────────────────────────────
with tab_color_tab:
    sec("7. Χρωματική Ανάλυση Φωτογραφιών")

    att_list = sorted(df_color["placeInfo/name"].dropna().unique())
    sel_c = st.selectbox("Επέλεξε αξιοθέατο", att_list, key="catt")
    grp = df_color[df_color["placeInfo/name"] == sel_c].copy()

    ca, cb, cc, cd = st.columns(4)
    kpi(ca, len(grp),                        "Φωτογραφίες")
    kpi(cb, f"{grp['S% mean'].mean():.1f}%", "Μέσος Κορεσμός S%")
    kpi(cc, f"{grp['V% mean'].mean():.1f}%", "Μέση Φωτεινότητα V%")
    kpi(cd, f"{grp['C mean'].mean():.1f}",   "Μέση Χρωματικότητα C")

    st.divider()

    # Palette strips
    sec("Παλέτα ανά εικόνα — κατανομή clusters")
    st.caption("Κάθε λωρίδα δείχνει τα 5 κυρίαρχα χρώματα σύμφωνα με το ποσοστό τους")
    max_n = st.slider("Αριθμός εικόνων", 5, min(60, len(grp)), min(20, len(grp)), key="pal_n")
    show  = grp.head(max_n).copy()
    show["lbl"] = show["Filename"].str[:28]

    fig_pal = go.Figure()
    for _, row in show.iterrows():
        for ci in range(1, 6):
            hx  = str(row.get(f"C{ci}_hex","")).strip()
            pct = float(row.get(f"C{ci}_pct", 0))
            nm  = str(row.get(f"C{ci}_name",""))
            if not hx or pct == 0:
                continue
            if not hx.startswith("#"):
                hx = "#" + hx
            tc = "black" if luminance(hx) > 140 else "white"
            fig_pal.add_trace(go.Bar(
                x=[pct], y=[row["lbl"]], orientation="h",
                marker_color=hx,
                text=f"{pct:.0f}%" if pct >= 9 else "",
                textfont_color=tc, textposition="inside",
                hovertemplate=f"{hx}<br>{nm}<br>{pct:.1f}%<extra></extra>",
                showlegend=False,
            ))
    fig_pal.update_layout(
        barmode="stack",
        height=max(60, max_n * 34),
        xaxis=dict(visible=False),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=170, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pal, use_container_width=True)

    st.divider()

    # 4-panel (ίδιο με screenshot)
    cl, cr = st.columns(2)
    with cl:
        sec("Κορεσμός vs Φωτεινότητα")
        st.caption("Κάθε σημείο = μία εικόνα")
        fig_sv = px.scatter(show, x="S% mean", y="V% mean",
                             hover_name="Filename", color="Color_temp",
                             color_discrete_map={"Ζεστό":"#e07b39","Ψυχρό":"#4a7fb5","Ουδέτερο":"#888"},
                             template="plotly_white",
                             labels={"S% mean":"Κορεσμός S%","V% mean":"Φωτεινότητα V%",
                                     "Color_temp":"Θερμ."})
        fig_sv.update_layout(height=300)
        st.plotly_chart(fig_sv, use_container_width=True)

    with cr:
        sec("Χρωματικότητα LCH (C mean)")
        st.caption("Πόσο «έγχρωμη» είναι κάθε εικόνα")
        fig_ch = px.bar(show, x="lbl", y="C mean",
                         color="C mean", color_continuous_scale="Oranges",
                         template="plotly_white",
                         labels={"lbl":"","C mean":"LCH Chroma"})
        fig_ch.update_layout(height=300, xaxis_tickangle=-35, coloraxis_showscale=False)
        st.plotly_chart(fig_ch, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Μέσες τιμές RGB ανά εικόνα")
        st.caption("Ισορροπία καναλιών χρώματος")
        fig_rgb = go.Figure()
        for ch, col_c in [("R mean","#e24847"),("G mean","#2e8b43"),("B mean","#2d4a6b")]:
            fig_rgb.add_trace(go.Bar(name=ch.split()[0], x=show["lbl"], y=show[ch],
                                      marker_color=col_c))
        fig_rgb.update_layout(barmode="group", template="plotly_white", height=300,
                               xaxis_tickangle=-35, yaxis_title="0-255",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_rgb, use_container_width=True)

    with cr:
        sec("Labspace: a* vs b* (χρωματικός άξονας)")
        st.caption("a*: πράσινο↔κόκκινο · b*: μπλε↔κίτρινο")
        lab = df_stats[df_stats["Space"]=="Lab"].copy()
        lab_pv = lab.pivot_table(index=["#","Filename"], columns="Channel", values="Mean").reset_index()
        if "a" in lab_pv.columns and "b" in lab_pv.columns:
            lab_g = lab_pv[lab_pv["#"].isin(show["#"].values)].merge(
                show[["#","lbl"]], on="#", how="left")
            fig_lab = px.scatter(lab_g, x="a", y="b", hover_name="lbl",
                                  color_discrete_sequence=["#2d4a6b"],
                                  template="plotly_white",
                                  labels={"a":"a* (πράσινο↔κόκκινο)","b":"b* (μπλε↔κίτρινο)"})
            fig_lab.add_hline(y=0, line_dash="dot", line_color="#ccc")
            fig_lab.add_vline(x=0, line_dash="dot", line_color="#ccc")
            fig_lab.update_layout(height=300)
            st.plotly_chart(fig_lab, use_container_width=True)

    st.divider()
    sec("Κατανομή χρωματικών οικογενειών (clusters)")
    all_names = []
    for ci in range(1,6):
        all_names.extend(grp[f"C{ci}_name"].dropna().tolist())
    cleaned = [re.sub(r"\b(very |dark |pale |light |vivid )","",n).strip() for n in all_names]
    fam_df = pd.DataFrame(Counter(cleaned).most_common(14), columns=["Οικογένεια","Count"])
    fig_fam = px.bar(fam_df, x="Count", y="Οικογένεια", orientation="h",
                     color="Count", color_continuous_scale="Blues",
                     template="plotly_white", text="Count")
    fig_fam.update_traces(textposition="outside")
    fig_fam.update_layout(height=400, yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig_fam, use_container_width=True)

    st.divider()
    sec("Σύγκριση όλων των αξιοθέατων — χρωματικοί δείκτες")
    all_sv = df_color.groupby("placeInfo/name")[
        ["S% mean","V% mean","C mean","R mean","G mean","B mean"]
    ].mean().reset_index()
    all_sv["Κατηγορία"] = all_sv["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    fig_cmp = px.scatter(all_sv, x="S% mean", y="V% mean", size="C mean",
                          color="Κατηγορία", color_discrete_map=CAT_COLOR,
                          hover_name="placeInfo/name", text="placeInfo/name",
                          template="plotly_white",
                          labels={"S% mean":"Κορεσμός S%","V% mean":"Φωτεινότητα V%"})
    fig_cmp.update_traces(textposition="top center", textfont_size=9)
    fig_cmp.update_layout(height=460,
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_cmp, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ΣΥΓΚΡΙΤΙΚΕΣ & ΠΡΟΒΛΕΠΤΙΚΕΣ
# ─────────────────────────────────────────────────────────────────────────────
with tab_cmp:
    sec("8. Συγκριτικές & Προβλεπτικές Αναλύσεις")

    cl, cr = st.columns(2)
    with cl:
        sec("Φυσικά vs Πολιτιστικά vs Δραστηριότητες")
        cat_r = rev_f.groupby("Category")["rating"].agg(["mean","std","count"]).reset_index()
        cat_r.columns = ["Κατηγορία","Μέση","Std","n"]
        fig = px.bar(cat_r, x="Κατηγορία", y="Μέση", error_y="Std",
                     color="Κατηγορία", color_discrete_map=CAT_COLOR,
                     template="plotly_white", text="Μέση", range_y=[3.5,5.5])
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Boxplot βαθμολογίας ανά κατηγορία")
        fig2 = px.box(rev_f, x="Category", y="rating",
                      color="Category", color_discrete_map=CAT_COLOR,
                      template="plotly_white",
                      labels={"Category":"Κατηγορία","rating":"Βαθμολογία"})
        fig2.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Βαθμολογία vs Αριθμός φωτογραφιών (ανά κριτική)")
    sc = rev_f[rev_f["Photocount"]<=15].copy()
    sc["lbl"] = sc["rating"].astype(str) + "★"
    fig3 = px.scatter(sc, x="Photocount", y="rating", color="lbl",
                      color_discrete_sequence=COLORS_R[::-1], opacity=0.5,
                      template="plotly_white",
                      labels={"Photocount":"Αριθμός φωτογραφιών","rating":"Βαθμολογία",
                              "lbl":"Βαθμολογία"})
    fig3.update_layout(height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig3, use_container_width=True)

    sec("Γραμμική τάση βαθμολογίας ανά έτος")
    ya = rev_f.groupby("year")["rating"].mean().reset_index().dropna()
    ya.columns = ["Έτος","Μέση"]
    if len(ya) >= 3:
        x_ = ya["Έτος"].values
        y_ = ya["Μέση"].values
        coeffs = np.polyfit(x_, y_, 1)
        x_ext  = np.array([x_.min(), x_.max()+3])
        y_ext  = np.polyval(coeffs, x_ext)
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=ya["Έτος"], y=ya["Μέση"],
                                   mode="markers+lines", name="Δεδομένα",
                                   line=dict(color="#2d4a6b")))
        fig4.add_trace(go.Scatter(x=x_ext, y=y_ext, mode="lines", name="Τάση",
                                   line=dict(color="#e07b39", dash="dash")))
        fig4.update_layout(template="plotly_white", height=300,
                            yaxis_range=[4.0,5.2],
                            xaxis_title="Έτος", yaxis_title="Μέση βαθμολογία")
        st.plotly_chart(fig4, use_container_width=True)
        direction = "ανοδική 📈" if coeffs[0]>0 else "καθοδική 📉"
        tip(f"Τάση: <b>{direction}</b> ({coeffs[0]:+.4f}/έτος). "
            f"Εκτίμηση {int(x_.max()+1)}: {np.polyval(coeffs, x_.max()+1):.2f}★")

    sec("Συσχέτιση χρωματικών δεικτών με βαθμολογία (Pearson r)")
    corr_cols = ["R mean","G mean","B mean","S% mean","V% mean","C mean","L mean"]
    mr = df_merged.dropna(subset=["rating"])
    corr_vals = mr[corr_cols+["rating"]].corr()["rating"].drop("rating").reset_index()
    corr_vals.columns = ["Δείκτης","r"]
    corr_vals = corr_vals.sort_values("r")
    fig5 = px.bar(corr_vals, x="r", y="Δείκτης", orientation="h",
                  color="r", color_continuous_scale="RdBu", range_color=[-0.3,0.3],
                  template="plotly_white", text="r")
    fig5.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig5.update_layout(height=300, yaxis_title="", coloraxis_showscale=False,
                        xaxis_range=[-0.4, 0.4])
    st.plotly_chart(fig5, use_container_width=True)
    tip("r κοντά στο +1/-1 = ισχυρή θετική/αρνητική συσχέτιση · r≈0 = καμία γραμμική σχέση.")

# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Kastoria Tourism Analytics · "
    f"Φωτογραφίες: {len(df_color):,} · "
    f"Κριτικές: {len(df_rev):,} · "
    f"Αξιοθέατα: {len(df_att):,}"
)
