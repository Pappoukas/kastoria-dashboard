"""
Kastoria Tourism Analytics — Streamlit Cloud Edition
=====================================================
Αρχεία: TripAdvisor_Kastoria_Backup.csv + Καστοριά_Αξιοθέατα.csv
Εκκίνηση: streamlit run app_cloud.py
"""

import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ── Page config ───────────────────────────────────────────────────────────────
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
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MONTH_GR = {1:"Ιαν",2:"Φεβ",3:"Μαρ",4:"Απρ",5:"Μάι",6:"Ιουν",
             7:"Ιουλ",8:"Αυγ",9:"Σεπ",10:"Οκτ",11:"Νοε",12:"Δεκ"}
TRIPTYPE_GR = {"COUPLES":"Ζευγάρια","FAMILY":"Οικογένεια","FRIENDS":"Φίλοι",
               "SOLO":"Μόνος","BUSINESS":"Επαγγελματικό","NONE":"—"}
LANG_MAP = {"el":"Ελληνικά","en":"Αγγλικά","ru":"Ρωσικά","it":"Ιταλικά",
            "nl":"Ολλανδικά","iw":"Εβραϊκά","fr":"Γαλλικά","de":"Γερμανικά"}
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
CAT_COLOR = {"Φυσικό":"#2e86ab","Πολιτιστικό":"#a23b72",
             "Δραστηριότητα":"#f18f01","Άλλο":"#888"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi(col, val, lbl):
    col.markdown(
        f'<div class="kpi"><div class="v">{val}</div>'
        f'<div class="l">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

def sec(title):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)

def save_upload(up):
    suf = ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suf) as t:
        t.write(up.read())
        return t.name

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_reviews(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)
    df["id"]            = pd.to_numeric(df["id"], errors="coerce")
    df["publishedDate"] = pd.to_datetime(df["publishedDate"], dayfirst=True, errors="coerce")
    df["travelDate"]    = pd.to_datetime(df["travelDate"], format="%Y-%m", errors="coerce")
    df["year"]          = df["publishedDate"].dt.year
    df["month"]         = df["publishedDate"].dt.month
    df["travelMonth"]   = df["travelDate"].dt.month
    df["lang_label"]    = df["lang"].map(LANG_MAP).fillna("Άλλη")
    df["tripType_gr"]   = df["tripType"].map(TRIPTYPE_GR).fillna("—")
    df["Category"]      = df["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    df["is_foreign"]    = df["lang"] != "el"
    df["has_photo"]     = df["Photocount"].fillna(0) > 0
    df["has_response"]  = df["ownerResponse/text"].notna()
    df["review_len"]    = df["text"].fillna("").apply(len)
    return df

@st.cache_data(show_spinner=False)
def load_attractions(path):
    df = pd.read_csv(path, encoding="utf-8-sig", sep=None, engine="python")
    df["placeInfo/latitude"]  = pd.to_numeric(
        df["placeInfo/latitude"].astype(str).str.replace(",","."), errors="coerce")
    df["placeInfo/longitude"] = pd.to_numeric(
        df["placeInfo/longitude"].astype(str).str.replace(",","."), errors="coerce")
    df["Category"] = df["placeInfo/name"].map(ATT_CATEGORY).fillna("Άλλο")
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ Kastoria Analytics")
    st.caption("Στατιστική ανάλυση κριτικών TripAdvisor")
    st.divider()

    st.markdown("### 📁 Αρχεία δεδομένων")
    up_rev = st.file_uploader("CSV κριτικών (.csv)",    type=["csv"], key="rev")
    up_att = st.file_uploader("CSV αξιοθέατων (.csv)", type=["csv"], key="att")

    def resolve(up, default):
        if up:
            return save_upload(up)
        if Path(default).exists():
            return default
        return None

    p_rev = resolve(up_rev, "TripAdvisor_Kastoria_Backup.csv")
    p_att = resolve(up_att, "Καστοριά_Αξιοθέατα.csv")

    missing = [n for n, p in [("CSV κριτικών", p_rev), ("CSV αξιοθέατων", p_att)] if not p]
    if missing:
        st.error("Λείπουν: " + ", ".join(missing))
        st.stop()

with st.spinner("Φόρτωση δεδομένων…"):
    df_rev = load_reviews(p_rev)
    df_att = load_attractions(p_att)

with st.sidebar:
    st.divider()
    st.markdown("### 🔍 Φίλτρα")

    all_att = sorted(df_rev["placeInfo/name"].dropna().unique())
    sel_att = st.multiselect("Αξιοθέατα", all_att, default=all_att)

    yrs = sorted(df_rev["year"].dropna().unique().astype(int))
    yr_range = st.slider("Έτος κριτικής",
                         int(min(yrs)), int(max(yrs)),
                         (int(min(yrs)), int(max(yrs))))

    sel_langs = st.multiselect(
        "Γλώσσα",
        sorted(df_rev["lang_label"].dropna().unique()),
        default=sorted(df_rev["lang_label"].dropna().unique()),
    )

rev = df_rev[
    df_rev["placeInfo/name"].isin(sel_att) &
    df_rev["year"].between(yr_range[0], yr_range[1]) &
    df_rev["lang_label"].isin(sel_langs)
]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dash, tab_pop, tab_rat, tab_geo, tab_trip, tab_inter = st.tabs([
    "📊 Dashboard",
    "📈 Δημοφιλία",
    "⭐ Βαθμολογίες",
    "🌍 Γλώσσα & Προέλευση",
    "👥 Τύπος Ταξιδιού",
    "📸 Αλληλεπίδραση",
])

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    sec("Επισκόπηση δεδομένων")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpi(c1, f"{len(rev):,}",                                "Κριτικές")
    kpi(c2, rev["placeInfo/name"].nunique(),                 "Αξιοθέατα")
    kpi(c3, f"{rev['rating'].mean():.2f}★",                  "Μέση βαθμολογία")
    kpi(c4, f"{(rev['rating']==5).mean()*100:.0f}%",         "5★ ποσοστό")
    kpi(c5, rev["lang_label"].nunique(),                     "Γλώσσες")
    kpi(c6, f"{rev['has_photo'].mean()*100:.0f}%",           "Με φωτογραφία")

    st.divider()
    cl, cr = st.columns(2)

    with cl:
        sec("Κριτικές ανά αξιοθέατο")
        d = rev["placeInfo/name"].value_counts().reset_index()
        d.columns = ["Αξιοθέατο","n"]
        d["Κατηγορία"] = d["Αξιοθέατο"].map(ATT_CATEGORY).fillna("Άλλο")
        fig = px.bar(d, x="n", y="Αξιοθέατο", orientation="h",
                     color="Κατηγορία", color_discrete_map=CAT_COLOR,
                     template="plotly_white", text="n")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=440, yaxis_title="", legend_title="Κατηγορία")
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Μέση βαθμολογία ανά αξιοθέατο")
        d2 = rev.groupby("placeInfo/name")["rating"].agg(["mean","count"]).reset_index()
        d2.columns = ["Αξιοθέατο","Μέση","n"]
        d2 = d2[d2["n"] >= 5].sort_values("Μέση")
        d2["Κατηγορία"] = d2["Αξιοθέατο"].map(ATT_CATEGORY).fillna("Άλλο")
        fig2 = px.bar(d2, x="Μέση", y="Αξιοθέατο", orientation="h",
                      color="Κατηγορία", color_discrete_map=CAT_COLOR,
                      template="plotly_white", text="Μέση", range_x=[3.5, 5.3])
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(height=440, yaxis_title="", legend_title="Κατηγορία")
        st.plotly_chart(fig2, use_container_width=True)

    # Χάρτης
    att_map = df_att.dropna(subset=["placeInfo/latitude","placeInfo/longitude"])
    if len(att_map) > 0:
        sec("Χάρτης αξιοθέατων")
        rc = rev["placeInfo/name"].value_counts().reset_index()
        rc.columns = ["placeInfo/name","Κριτικές"]
        map_df = att_map.merge(rc, on="placeInfo/name", how="left")
        map_df["Κριτικές"] = map_df["Κριτικές"].fillna(5)
        fig_map = px.scatter_mapbox(
            map_df,
            lat="placeInfo/latitude", lon="placeInfo/longitude",
            hover_name="placeInfo/name", size="Κριτικές",
            color="Category", color_discrete_map=CAT_COLOR,
            size_max=30, zoom=13, mapbox_style="open-street-map",
        )
        fig_map.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0),
                               legend_title="Κατηγορία")
        st.plotly_chart(fig_map, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ΔΗΜΟΦΙΛΙΑ
# ══════════════════════════════════════════════════════════════════════════════
with tab_pop:
    sec("1. Δημοφιλία & Επισκεψιμότητα")

    cl, cr = st.columns(2)
    with cl:
        sec("Χρονική εξέλιξη κριτικών")
        monthly = rev.groupby(["year","month"]).size().reset_index(name="n")
        monthly["date"] = pd.to_datetime(monthly[["year","month"]].assign(day=1))
        fig = px.line(monthly.sort_values("date"), x="date", y="n",
                      template="plotly_white", labels={"date":"","n":"Κριτικές"})
        fig.update_traces(line_color="#2d4a6b", line_width=2)
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Εποχικότητα — μήνας ταξιδιού")
        seas = rev.groupby("travelMonth").size().reset_index(name="n").dropna()
        seas["lbl"] = seas["travelMonth"].apply(lambda m: MONTH_GR.get(int(m),""))
        fig2 = px.bar(seas, x="lbl", y="n", color="n",
                      color_continuous_scale="Blues", template="plotly_white",
                      text="n", labels={"lbl":"","n":"Κριτικές"})
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=280, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Κριτικές ανά έτος — top αξιοθέατα")
    top8 = rev["placeInfo/name"].value_counts().head(8).index.tolist()
    yrly = rev[rev["placeInfo/name"].isin(top8)].groupby(
        ["year","placeInfo/name"]).size().reset_index(name="n")
    fig3 = px.line(yrly, x="year", y="n", color="placeInfo/name",
                   markers=True, template="plotly_white",
                   labels={"year":"Έτος","n":"Κριτικές","placeInfo/name":"Αξιοθέατο"})
    fig3.update_layout(height=320,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Χρόνος ζωής κριτικών ανά αξιοθέατο")
        span = rev.groupby("placeInfo/name")["publishedDate"].agg(["min","max"]).reset_index()
        span.columns = ["Αξιοθέατο","Πρώτη","Τελευταία"]
        span = span.dropna().sort_values("Πρώτη")
        fig4 = px.timeline(span.assign(Task=span["Αξιοθέατο"]),
                           x_start="Πρώτη", x_end="Τελευταία", y="Αξιοθέατο",
                           color="Αξιοθέατο", template="plotly_white")
        fig4.update_layout(height=380, showlegend=False, yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Heatmap κριτικών (έτος × μήνας)")
        hm = rev.groupby(["year","month"]).size().reset_index(name="n").dropna()
        hm["lbl"] = hm["month"].apply(lambda m: MONTH_GR.get(int(m),""))
        pivot = hm.pivot(index="year", columns="lbl", values="n").fillna(0)
        col_order = [v for v in MONTH_GR.values() if v in pivot.columns]
        pivot = pivot.reindex(columns=col_order)
        fig5 = px.imshow(pivot, color_continuous_scale="Blues",
                         aspect="auto", text_auto=True, template="plotly_white",
                         labels=dict(x="Μήνας", y="Έτος", color="Κριτικές"))
        fig5.update_layout(height=380)
        st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ΒΑΘΜΟΛΟΓΙΕΣ
# ══════════════════════════════════════════════════════════════════════════════
with tab_rat:
    sec("2. Ικανοποίηση & Βαθμολογίες")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή βαθμολογιών")
        rd = rev["rating"].value_counts().sort_index().reset_index()
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
        trend = rev.groupby("year")["rating"].agg(["mean","count"]).reset_index()
        trend.columns = ["Έτος","Μέση","n"]
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(x=trend["Έτος"], y=trend["n"],
                               name="Κριτικές", marker_color="#b8d4f5"),
                        secondary_y=False)
        fig2.add_trace(go.Scatter(x=trend["Έτος"], y=trend["Μέση"],
                                   name="Μέση βαθμ.",
                                   line=dict(color="#e07b39", width=2),
                                   mode="lines+markers"),
                        secondary_y=True)
        fig2.update_layout(template="plotly_white", height=290,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig2.update_yaxes(title_text="Κριτικές", secondary_y=False)
        fig2.update_yaxes(title_text="Βαθμ.", range=[4.0, 5.2], secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Κατανομή βαθμολογιών ανά αξιοθέατο")
    rat_att = rev.groupby(["placeInfo/name","rating"]).size().reset_index(name="n")
    rat_att["lbl"] = rat_att["rating"].astype(str) + "★"
    fig3 = px.bar(rat_att, x="n", y="placeInfo/name", color="lbl",
                  barmode="relative", orientation="h",
                  color_discrete_sequence=COLORS_R[::-1],
                  template="plotly_white",
                  labels={"n":"Κριτικές","placeInfo/name":"","lbl":"Βαθμολογία"})
    fig3.update_layout(height=420, yaxis_title="")
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Βαθμολογία ανά κατηγορία αξιοθέατου")
        cat_r = rev.groupby("Category")["rating"].agg(["mean","std"]).reset_index()
        cat_r.columns = ["Κατηγορία","Μέση","Std"]
        fig4 = px.bar(cat_r, x="Κατηγορία", y="Μέση", error_y="Std",
                      color="Κατηγορία", color_discrete_map=CAT_COLOR,
                      template="plotly_white", text="Μέση", range_y=[3.5, 5.5])
        fig4.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig4.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Μήνας ταξιδιού vs Βαθμολογία")
        sm = rev.groupby("travelMonth")["rating"].mean().reset_index().dropna()
        sm["lbl"] = sm["travelMonth"].apply(lambda m: MONTH_GR.get(int(m), ""))
        fig5 = px.bar(sm, x="lbl", y="rating", color="rating",
                      color_continuous_scale="RdYlGn", range_color=[4.0, 5.0],
                      template="plotly_white", text="rating",
                      labels={"lbl":"","rating":"Μέση βαθμολογία"},
                      range_y=[3.8, 5.2])
        fig5.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig5.update_layout(height=300, coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

    sec("Βαθμολογία ανά τύπο ταξιδιού")
    trip_r = rev[rev["tripType_gr"] != "—"].groupby("tripType_gr")["rating"].agg(
        ["mean","count"]).reset_index()
    trip_r.columns = ["Τύπος","Μέση","n"]
    trip_r = trip_r.sort_values("Μέση")
    fig6 = px.bar(trip_r, x="Τύπος", y="Μέση",
                  color="Μέση", color_continuous_scale="RdYlGn",
                  range_color=[4.0, 5.0], template="plotly_white",
                  text="Μέση", range_y=[4.0, 5.2])
    fig6.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig6.update_layout(coloraxis_showscale=False, height=300)
    st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ΓΛΩΣΣΑ & ΠΡΟΕΛΕΥΣΗ
# ══════════════════════════════════════════════════════════════════════════════
with tab_geo:
    sec("4. Γλωσσική & Γεωγραφική Προέλευση")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή γλωσσών")
        ld = rev["lang_label"].value_counts().reset_index()
        ld.columns = ["Γλώσσα","n"]
        fig = px.pie(ld, values="n", names="Γλώσσα", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     template="plotly_white")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Μέση βαθμολογία ανά γλώσσα")
        lr = rev.groupby("lang_label")["rating"].agg(["mean","count"]).reset_index()
        lr.columns = ["Γλώσσα","Μέση","n"]
        lr = lr[lr["n"] >= 3].sort_values("Μέση")
        fig2 = px.bar(lr, x="Γλώσσα", y="Μέση",
                      color="Μέση", color_continuous_scale="RdYlGn",
                      range_color=[4.0, 5.0], template="plotly_white",
                      text="Μέση", range_y=[3.5, 5.3])
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, height=300,
                            xaxis_tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Ξενόγλωσσες κριτικές ανά αξιοθέατο (%)")
    fg = rev.groupby("placeInfo/name")["is_foreign"].agg(["sum","count"]).reset_index()
    fg.columns = ["Αξιοθέατο","Ξένες","Σύνολο"]
    fg["Ποσοστό %"] = (fg["Ξένες"] / fg["Σύνολο"] * 100).round(1)
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
        la = rev.groupby(["placeInfo/name","lang_label"]).size().reset_index(name="n")
        pv = la.pivot(index="placeInfo/name", columns="lang_label",
                      values="n").fillna(0)
        fig4 = px.imshow(pv, color_continuous_scale="Blues", aspect="auto",
                         text_auto=True, template="plotly_white",
                         labels=dict(x="Γλώσσα", y="Αξιοθέατο", color="Κριτικές"))
        fig4.update_layout(height=420)
        st.plotly_chart(fig4, use_container_width=True)

    with cr:
        sec("Top 20 πόλεις προέλευσης")
        loc = rev["user/userLocation/name"].value_counts().head(20).reset_index()
        loc.columns = ["Τοποθεσία","n"]
        fig5 = px.bar(loc, x="n", y="Τοποθεσία", orientation="h",
                      color="n", color_continuous_scale="Blues",
                      template="plotly_white", text="n")
        fig5.update_traces(textposition="outside")
        fig5.update_layout(height=420, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ΤΥΠΟΣ ΤΑΞΙΔΙΟΥ
# ══════════════════════════════════════════════════════════════════════════════
with tab_trip:
    sec("5. Τύπος Ταξιδιού & Προτιμήσεις")

    cl, cr = st.columns(2)
    with cl:
        sec("Κατανομή τύπου ταξιδιού")
        td = rev[rev["tripType_gr"] != "—"]["tripType_gr"].value_counts().reset_index()
        td.columns = ["Τύπος","n"]
        fig = px.pie(td, values="n", names="Τύπος", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     template="plotly_white")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Βαθμολογία ανά τύπο ταξιδιού")
        fig2 = px.box(rev[rev["tripType_gr"] != "—"],
                      x="tripType_gr", y="rating",
                      color="tripType_gr",
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      template="plotly_white",
                      labels={"tripType_gr":"","rating":"Βαθμολογία"})
        fig2.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig2, use_container_width=True)

    sec("Heatmap: τύπος ταξιδιού × αξιοθέατο")
    tp = rev[rev["tripType_gr"] != "—"].groupby(
        ["placeInfo/name","tripType_gr"]).size().reset_index(name="n")
    hm = tp.pivot(index="placeInfo/name", columns="tripType_gr",
                  values="n").fillna(0)
    fig3 = px.imshow(hm, color_continuous_scale="Purples", aspect="auto",
                     text_auto=True, template="plotly_white",
                     labels=dict(x="Τύπος", y="Αξιοθέατο", color="Κριτικές"))
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

    cl, cr = st.columns(2)
    for col, trip in [(cl, "Οικογένεια"), (cr, "Ζευγάρια")]:
        with col:
            sub = (rev[rev["tripType_gr"] == trip]["placeInfo/name"]
                   .value_counts().head(8).reset_index())
            sub.columns = ["Αξιοθέατο","n"]
            ft = px.bar(sub, x="n", y="Αξιοθέατο", orientation="h",
                        color="n", color_continuous_scale="Blues",
                        template="plotly_white", text="n",
                        title=f"Top αξιοθέατα — {trip}")
            ft.update_traces(textposition="outside")
            ft.update_layout(height=300, yaxis_title="", coloraxis_showscale=False)
            st.plotly_chart(ft, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ΑΛΛΗΛΕΠΙΔΡΑΣΗ
# ══════════════════════════════════════════════════════════════════════════════
with tab_inter:
    sec("6. Αλληλεπίδραση & Δραστηριότητα Χρηστών")

    cl, cr = st.columns(2)
    with cl:
        sec("Αριθμός φωτογραφιών ανά βαθμολογία")
        ph = rev.groupby("rating")["Photocount"].mean().reset_index()
        ph.columns = ["Βαθμολογία","Μέσος αρ."]
        fig = px.bar(ph, x="Βαθμολογία", y="Μέσος αρ.",
                     color="Μέσος αρ.", color_continuous_scale="Blues",
                     template="plotly_white", text="Μέσος αρ.")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with cr:
        sec("Helpful votes ανά βαθμολογία")
        hv = rev.groupby("rating")["helpfulVotes"].mean().reset_index()
        hv.columns = ["Βαθμολογία","Μέσα votes"]
        fig2 = px.bar(hv, x="Βαθμολογία", y="Μέσα votes",
                      color="Μέσα votes", color_continuous_scale="Greens",
                      template="plotly_white", text="Μέσα votes")
        fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, height=280)
        st.plotly_chart(fig2, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        sec("Απαντήσεις διαχειριστών ανά αξιοθέατο (%)")
        rsp = rev.groupby("placeInfo/name")["has_response"].agg(["sum","count"]).reset_index()
        rsp.columns = ["Αξιοθέατο","Απαντ.","Σύνολο"]
        rsp["Ποσοστό %"] = (rsp["Απαντ."] / rsp["Σύνολο"] * 100).round(1)
        rsp = rsp[rsp["Σύνολο"] >= 5].sort_values("Ποσοστό %", ascending=False)
        fig3 = px.bar(rsp, x="Ποσοστό %", y="Αξιοθέατο", orientation="h",
                      color="Ποσοστό %", color_continuous_scale="Teal",
                      template="plotly_white", text="Ποσοστό %")
        fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig3.update_layout(height=380, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with cr:
        sec("Μέγεθος κριτικής vs Βαθμολογία")
        rl = rev[rev["review_len"] < 3000].copy()
        rl["lbl"] = rl["rating"].astype(str) + "★"
        fig4 = px.box(rl, x="lbl", y="review_len",
                      color="lbl",
                      color_discrete_sequence=COLORS_R[::-1],
                      template="plotly_white",
                      labels={"review_len":"Χαρακτήρες","lbl":""})
        fig4.update_layout(showlegend=False, height=340)
        st.plotly_chart(fig4, use_container_width=True)

    sec("Κριτικές με/χωρίς φωτογραφία ανά βαθμολογία")
    ph2 = rev.groupby(["rating","has_photo"]).size().reset_index(name="n")
    ph2["Φωτ."] = ph2["has_photo"].map({True:"Με φωτ.", False:"Χωρίς φωτ."})
    fig5 = px.bar(ph2, x="rating", y="n", color="Φωτ.", barmode="group",
                  template="plotly_white",
                  color_discrete_map={"Με φωτ.":"#2d4a6b","Χωρίς φωτ.":"#b8d4f5"},
                  labels={"rating":"Βαθμολογία","n":"Κριτικές"})
    fig5.update_layout(height=280)
    st.plotly_chart(fig5, use_container_width=True)

    sec("Αριθμός κριτικών ανά επίπεδο εμπλοκής χρήστη")
    rev["contrib_group"] = pd.cut(
        rev["user/contributions/totalContributions"].fillna(0),
        bins=[0, 1, 5, 20, 100, 99999],
        labels=["1 κριτική","2-5","6-20","21-100","100+"],
    )
    cg = rev.groupby("contrib_group", observed=True).agg(
        Κριτικές=("rating","count"),
        Μέση_βαθμ=("rating","mean"),
    ).reset_index()
    cg.columns = ["Εμπειρία χρήστη","Κριτικές","Μέση βαθμολογία"]
    fig6 = make_subplots(specs=[[{"secondary_y": True}]])
    fig6.add_trace(go.Bar(x=cg["Εμπειρία χρήστη"], y=cg["Κριτικές"],
                           name="Κριτικές", marker_color="#b8d4f5"),
                    secondary_y=False)
    fig6.add_trace(go.Scatter(x=cg["Εμπειρία χρήστη"], y=cg["Μέση βαθμολογία"],
                               name="Μέση βαθμολογία",
                               line=dict(color="#e07b39", width=2),
                               mode="lines+markers"),
                    secondary_y=True)
    fig6.update_layout(template="plotly_white", height=300,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        xaxis_title="Εμπειρία χρήστη (αριθμός συνολικών κριτικών)")
    fig6.update_yaxes(title_text="Κριτικές", secondary_y=False)
    fig6.update_yaxes(title_text="Βαθμολογία", range=[4.0, 5.3], secondary_y=True)
    st.plotly_chart(fig6, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Kastoria Tourism Analytics · "
    f"Κριτικές: {len(df_rev):,} · "
    f"Αξιοθέατα: {df_rev['placeInfo/name'].nunique()}"
)
