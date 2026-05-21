import streamlit as st
import random
import string
import time
import hashlib
from streamlit_autorefresh import st_autorefresh

def theme_colors():
    dark = st.session_state.get("theme", "dark") == "dark"

    return {
        "bg": "#09090f" if dark else "#f6f7fb",
        "card_bg": "#13131f" if dark else "#ffffff",
        "border": "#25253a" if dark else "#dcdcec",
        "text": "#f0f0ff" if dark else "#111827",
        "subtext": "#8888aa" if dark else "#667085",
        "secondary": "#1e1e30" if dark else "#ececf5",
    }

st.set_page_config(
    page_title="SyncUp", page_icon="⚡",
    layout="centered", initial_sidebar_state="collapsed",
)

# ── Theme State ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = (
        "light"
        if st.session_state.theme == "dark"
        else "dark"
    )

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── Data layer ────────────────────────────────────────────────────────────────
def load_session(code):
    try:
        r = get_sb().table("sessions").select("*").eq("code", code).execute()
        if r.data:
            row = r.data[0]
            return {
                "topic":       row["topic"],
                "members":     row.get("members") or [],
                "timer_state": row.get("timer_state"),
            }
    except Exception as e:
        st.error(f"DB error: {e}")
    return None

def load_timer_only(code):
    """Lightweight fetch — only timer_state + member count."""
    try:
        r = get_sb().table("sessions").select("timer_state,members").eq("code", code).execute()
        if r.data:
            row = r.data[0]
            return row.get("timer_state"), len(row.get("members") or [])
    except Exception:
        pass
    return None, 0

def create_session(code, topic):
    try:
        get_sb().table("sessions").insert({
            "code": code, "topic": topic,
            "members": [], "timer_state": None,
            "created_at": int(time.time()),
        }).execute()
        return True
    except Exception as e:
        st.error(f"DB error: {e}")
        return False

def add_member(code, member):
    try:
        sess = load_session(code)
        if not sess: return False
        members = [m for m in sess["members"] if m.get("nama") != member["nama"]]
        members.append(member)
        get_sb().table("sessions").update({"members": members}).eq("code", code).execute()
        return True
    except Exception as e:
        st.error(f"DB error: {e}")
        return False

def save_timer(code, state):
    try:
        get_sb().table("sessions").update({"timer_state": state}).eq("code", code).execute()
    except Exception as e:
        st.error(f"DB error: {e}")

def gen_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

# ── Role resolver (no duplicates) ─────────────────────────────────────────────
FALLBACK_ROLES = ["Moderator", "Notulen", "Timekeeper", "Summarizer", "Reviewer", "Flexible"]

def resolve_roles(members):
    if not members: return {}
    seed = "".join(sorted(m.get("nama", "") for m in members))
    rng  = random.Random(int(hashlib.md5(seed.encode()).hexdigest(), 16))
    assigned, used = {}, set()
    for m in members:
        r = (m.get("role") or "Flexible").strip()
        if r not in used:
            assigned[m["nama"]] = r
            used.add(r)
        else:
            avail = [x for x in FALLBACK_ROLES if x not in used] or ["Flexible"]
            nr = rng.choice(avail)
            assigned[m["nama"]] = nr
            used.add(nr)
    return assigned

# ── Agenda builder ────────────────────────────────────────────────────────────
def build_agenda(sess):
    members = sess.get("members", [])
    prioritas, kendala = [], []
    max_waktu = 60

    for m in members:
        if m.get("bahas"):   prioritas.append(m["bahas"])
        if m.get("kendala"): kendala.append(m["kendala"])
        try: max_waktu = max(max_waktu, int(m.get("waktu", 60)))
        except: pass

    prioritas = list(dict.fromkeys(prioritas))
    kendala   = list(dict.fromkeys(kendala))

    # Alur based on actual topics (no generic opening/closing)
    if prioritas:
        n         = len(prioritas)
        avail     = max(max_waktu - 5, n * 10)
        per_topic = max(10, avail // n)
        alur = [{"label": p, "menit": per_topic} for p in prioritas]
        alur.append({"label": "Wrap-up & next steps", "menit": 5})
    else:
        alur = [
            {"label": "Diskusi utama", "menit": max_waktu - 5},
            {"label": "Wrap-up",       "menit": 5},
        ]

    return {
        "prioritas": prioritas, "kendala": kendala,
        "alur": alur, "roles": resolve_roles(members),
    }

# ── Dynamic CSS ───────────────────────────────────────────────────────────────
def get_css():

    dark = st.session_state.theme == "dark"

    bg          = "#09090f" if dark else "#f6f7fb"
    card_bg     = "#13131f" if dark else "#ffffff"
    border      = "#25253a" if dark else "#dcdcec"

    # TEXT
    text        = "#f0f0ff" if dark else "#111827"
    subtext     = "#8888aa" if dark else "#667085"

    secondary   = "#1e1e30" if dark else "#ececf5"

    return f"""
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>

#MainMenu,
footer,
header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]{{
    display:none!important
}}

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main{{
    background:{bg}!important;
    transition:all .25s ease;
}}

/* FORCE ALL TEXT */
body,
p,
span,
label,
div,
h1,
h2,
h3,
h4,
h5,
h6{{
    color:{text}!important;
}}

[data-testid="block-container"]{{
    max-width:460px!important;
    padding:24px 16px 80px!important;
    margin:0 auto!important
}}

*,*::before,*::after{{
    font-family:'Plus Jakarta Sans',sans-serif!important;
    box-sizing:border-box
}}

.stTextInput input,
.stNumberInput input{{
    background:{card_bg}!important;
    border:1.5px solid {border}!important;
    border-radius:12px!important;
    color:{text}!important;
    font-size:14px!important;
    padding:12px 16px!important;
}}

.stTextInput input::placeholder,
.stNumberInput input::placeholder{{
    color:{subtext}!important;
}}

.stTextInput label,
.stNumberInput label,
.stRadio>label{{
    color:{subtext}!important;
    font-size:12px!important;
    font-weight:600!important;
    letter-spacing:.4px!important;
    text-transform:uppercase!important
}}

[data-testid="stRadio"]>div{{
    gap:8px!important;
    flex-direction:column!important
}}

[data-testid="stRadio"]>div>label{{
    background:{card_bg}!important;
    border:1.5px solid {border}!important;
    border-radius:12px!important;
    padding:11px 16px!important;
    color:{text}!important;
    font-size:14px!important;
    font-weight:500!important;
}}

[data-testid="stRadio"]>div>label:has(input:checked){{
    border-color:#ff6b35!important;
    background:rgba(255,107,53,.1)!important;
    color:#ff6b35!important
}}

.stButton>button{{
    background:linear-gradient(135deg,#ff6b35,#e85420)!important;
    color:#fff!important;
    border:none!important;
    border-radius:14px!important;
    padding:14px 24px!important;
    font-size:15px!important;
    font-weight:700!important;
    width:fit-content!important;
}}

.ghost .stButton>button{{
    background:{card_bg}!important;
    border:1.5px solid {border}!important;
    color:{subtext}!important;
    box-shadow:none!important
}}

.stNumberInput button{{
    background:{card_bg}!important;
    border:1.5px solid {border}!important;
    border-radius:8px!important;
    color:{text}!important
}}

.stProgress>div>div>div>div{{
    background:#ff6b35!important;
    border-radius:99px!important
}}

.stProgress>div>div>div{{
    background:{secondary}!important;
    border-radius:99px!important
}}

[data-testid="stAlert"]{{
    background:rgba(255,107,53,.08)!important;
    border:1px solid rgba(255,107,53,.2)!important;
    border-radius:12px!important;
    color:{text}!important
}}

[data-testid="stCode"] pre{{
    background:{card_bg}!important;
    border:1.5px dashed {border}!important;
    border-radius:12px!important;
    color:{text}!important;
}}

hr{{
    border-color:{border}!important
}}

[data-testid="column"]{{
    padding:0 4px!important
}}

/* CARD TEXT FIX */
.card-text,
.card-text * {{
    color:{text}!important;
}}

</style>
"""

# ── HTML helpers ──────────────────────────────────────────────────────────────
def chip(t):

    c = theme_colors()

    return f'''
    <div style="
        display:inline-block;
        background:rgba(255,107,53,.12);
        color:#ff6b35;
        border-radius:99px;
        padding:4px 14px;
        font-size:11px;
        font-weight:700;
        letter-spacing:1.5px;
        text-transform:uppercase;
        margin-bottom:16px;">
        {t}
    </div>
    '''

def h1(t, size="28px"):

    c = theme_colors()

    return f'''
    <h1 style="
        font-size:{size};
        font-weight:800;
        color:{c["text"]};
        line-height:1.2;
        margin:0 0 8px;">
        {t}
    </h1>
    '''

def sub(t):

    c = theme_colors()

    return f'''
    <p style="
        color:{c["subtext"]};
        font-size:14px;
        line-height:1.7;
        margin:0 0 28px;">
        {t}
    </p>
    '''

def sec(t):

    return f'''
    <p style="
        font-size:11px;
        font-weight:700;
        color:#ff6b35;
        letter-spacing:1.5px;
        text-transform:uppercase;
        margin:0 0 10px;">
        {t}
    </p>
    '''

def card(content, bg=None, border=None, pad="20px 18px"):
    c      = theme_colors()
    bg     = bg     or c["card_bg"]
    border = border or c["border"]
    text   = c["text"]
    return f'''
    <div style="
        background:{bg};
        border:1.5px solid {border};
        border-radius:14px;
        padding:{pad};
        margin-bottom:8px;
        color:{text};
    ">
        {content}
    </div>
    '''

def badge(t):

    return f'''
    <span style="
        background:rgba(255,107,53,.12);
        color:#ff6b35;
        border-radius:6px;
        padding:3px 10px;
        font-size:12px;
        font-weight:600;">
        {t}
    </span>
    '''

def pill(t):

    c = theme_colors()

    return f'''
    <div style="
        display:inline-block;
        background:{c["secondary"]};
        border-radius:99px;
        padding:5px 14px;
        font-size:12px;
        font-weight:700;
        color:{c["subtext"]};
        margin-bottom:16px;
    ">
        {t}
    </div>
    '''

def sp(h=8):
    st.markdown(
        f"<div style='height:{h}px'></div>",
        unsafe_allow_html=True
    )

# ── Navigation ────────────────────────────────────────────────────────────────
def nav(page):
    st.session_state.page = page
    try:
        if st.session_state.get("session_code"):
            st.query_params["code"] = st.session_state["session_code"]
        st.query_params["pg"] = page
    except: pass
    st.rerun()

# ── URL restore on page refresh ───────────────────────────────────────────────
def init_from_url():
    if "page" in st.session_state:
        return
    params = st.query_params
    code   = params.get("code", "")
    page   = params.get("pg",   "")
    if code:
        sess = load_session(code)
        if sess:
            st.session_state.session_code  = code
            st.session_state.session_topic = sess["topic"]
            st.session_state.agenda        = build_agenda(sess)
            st.session_state.alur_index    = 0
            if page in ("agenda", "timer"):
                st.session_state.page = page
                return
    st.session_state.page = "landing"

# ── Pages ─────────────────────────────────────────────────────────────────────

def page_landing():
    try: st.query_params.clear()
    except: pass
    st.markdown("""
    <div style="text-align:center;padding:48px 0 32px;">
        <div style="font-size:52px;margin-bottom:12px;">⚡</div>
        <div style="font-size:36px;font-weight:800;color:{text};letter-spacing:-1px;">
            Sync<span style="color:#ff6b35;">Up</span></div>
        <p style="color:{subtext};font-size:14px;margin:10px 0 0;line-height:1.7;">
            Bantu kelompokmu mulai sesi<br>dengan arah yang jelas.</p>
    </div>""", unsafe_allow_html=True)
    if st.button("⚡  Buat Sesi Baru"): nav("buat_step1")
    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("🔗  Gabung Sesi"): nav("gabung")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-top:48px;color:#2e2e44;font-size:12px;">Tidak ada yang jadi pemimpin. Semua berkontribusi.</div>', unsafe_allow_html=True)


def page_buat_step1():
    st.markdown(chip("Langkah 1 / 2"), unsafe_allow_html=True)
    st.markdown(h1("Siapkan Sesi Bareng"), unsafe_allow_html=True)
    st.markdown(sub("Semua anggota akan mengisi fokus masing-masing sebelum sesi dimulai"), unsafe_allow_html=True)
    topic = st.text_input("HARI INI MAU BAHAS ATAU KERJAIN APA?",
                          placeholder="contoh: Latihan statistik / Revisi proposal", key="input_topic")
    sp(12)
    if st.button("Lanjut dan Buat Link →"):
        if topic.strip():
            code = gen_code()
            if create_session(code, topic.strip()):
                st.session_state.session_code  = code
                st.session_state.session_topic = topic.strip()
                nav("buat_step2")
        else:
            st.error("Isi topik sesi dulu ya!")
    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_b1"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)


def page_buat_step2():
    code  = st.session_state.get("session_code", "")
    topic = st.session_state.get("session_topic", "")

    st.markdown(chip("Langkah 2 / 2"), unsafe_allow_html=True)
    st.markdown(h1("Ajak Teman Masuk"), unsafe_allow_html=True)
    st.markdown(sub("Bagikan kode ini ke anggota, lalu kamu juga isi inputmu"), unsafe_allow_html=True)

    st.markdown(sec("Topik Sesi"), unsafe_allow_html=True)
    colors = theme_colors()
    text = colors["text"]
    st.markdown(card(f'<span style="color:{text};font-size:14px;font-weight:600;">{topic}</span>',
                     bg="rgba(255,107,53,.07)", border="rgba(255,107,53,.18)"), unsafe_allow_html=True)
    sp(8)
    st.markdown(sec("Kode Sesi — Bagikan ke Anggota"), unsafe_allow_html=True)
    st.code(code.upper())
    st.info(f"💡 Anggota buka app → klik **Gabung Sesi** → masukkan kode **{code.upper()}**")
    sp(16)

    # ── Nama ketua (editable) ──
    st.markdown(sec("Nama Kamu"), unsafe_allow_html=True)
    nama_ketua = st.text_input("", placeholder="contoh: Raka", key="ketua_nama", label_visibility="collapsed")
    sp(8)

    # ── Member count ──
    sess = load_session(code)
    n    = len(sess["members"]) if sess else 0
    if n:
        st.markdown(pill(f"👥 {n} anggota sudah mengisi"), unsafe_allow_html=True)

    if st.button("✍️  Isi Input Sesi"):
        if nama_ketua.strip():
            st.session_state.member_nama      = nama_ketua.strip()
            st.session_state.joining_as_ketua = True
            nav("gabung_form")
        else:
            st.error("Isi nama kamu dulu ya!")

    if n:
        sp()
        if st.button("🎯  Lihat Agenda Sesi"):
            st.session_state.agenda     = build_agenda(sess)
            st.session_state.alur_index = 0
            nav("agenda")

    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_b2"): nav("buat_step1")
        st.markdown("</div>", unsafe_allow_html=True)


def page_gabung():
    st.markdown(h1("Gabung Sesi"), unsafe_allow_html=True)
    st.markdown(sub("Masuk dulu sebelum ikut menyusun agenda sesi bareng"), unsafe_allow_html=True)
    nama = st.text_input("NAMA", placeholder="contoh: Aby", key="g_nama")
    kode = st.text_input("KODE SESI", placeholder="contoh: abc123", key="g_kode")
    sp(12)
    if st.button("Selanjutnya →"):
        if nama.strip() and kode.strip():
            raw  = kode.strip().split("/")[-1].lower().strip()
            sess = load_session(raw)
            if sess:
                st.session_state.session_code     = raw
                st.session_state.member_nama      = nama.strip()
                st.session_state.session_topic    = sess["topic"]
                st.session_state.joining_as_ketua = False
                nav("gabung_form")
            else:
                st.error("Kode sesi tidak ditemukan. Cek lagi ya!")
        else:
            st.error("Isi nama dan kode sesi dulu!")
    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_g"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)


def page_gabung_form():
    code  = st.session_state.get("session_code", "")
    topic = st.session_state.get("session_topic", "")
    nama  = st.session_state.get("member_nama", "Anggota")

    sess = load_session(code)
    n    = len(sess["members"]) if sess else 0

    st.markdown(pill(f"✍️  {nama}  ·  {n} sudah mengisi"), unsafe_allow_html=True)
    st.markdown(h1(topic, size="22px"), unsafe_allow_html=True)
    st.markdown(sub("Semua jawaban anggota akan digabung otomatis menjadi agenda sesi bareng"), unsafe_allow_html=True)

    bahas   = st.text_input("HAL APA YANG MENURUTMU PERLU DIBAHAS DULU?",
                             placeholder="contoh: pembagian tugas presentasi", key="f_bahas")
    kendala = st.text_input("ADA KENDALA ATAU HAL YANG PERLU DIKLARIFIKASI?",
                             placeholder="contoh: belum bagi role / deadline mepet", key="f_kendala")
    waktu   = st.number_input("HARI INI KAMU AVAILABLE BERAPA LAMA? (MENIT)",
                               min_value=15, max_value=300, value=60, step=15, key="f_waktu")

    # ── Role with "Lainnya" custom input ──
    role_options = ["Catet poin penting", "Time keeper", "Jelasin ide", "Flexible", "Lainnya"]
    role_sel = st.radio("KAMU NYAMAN BANTU DI BAGIAN...", role_options, key="f_role")

    final_role = role_sel
    if role_sel == "Lainnya":
        custom = st.text_input("Tulis role kamu:",
                                placeholder="contoh: Dokumentasi, Desain, Presentasi...",
                                key="f_role_custom")
        final_role = custom.strip() if custom.strip() else "Flexible"

    sp(16)

    if st.button("Susun Agenda →"):
        if bahas.strip():
            ok = add_member(code, {
                "nama": nama, "bahas": bahas.strip(),
                "kendala": kendala.strip(), "waktu": int(waktu), "role": final_role,
            })
            if ok:
                sess = load_session(code)
                st.session_state.agenda     = build_agenda(sess)
                st.session_state.alur_index = 0
                nav("agenda")
        else:
            st.error("Isi minimal satu topik yang ingin dibahas!")

    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali", key="back_f"):
            nav("buat_step2" if st.session_state.get("joining_as_ketua") else "gabung")
        st.markdown("</div>", unsafe_allow_html=True)


def page_agenda():
    code   = st.session_state.get("session_code", "")
    agenda = st.session_state.get("agenda", {})
 
    sess      = load_session(code)
    n_members = len(sess["members"]) if sess else 0
 
    # Auto refresh tiap 10 detik
    st_autorefresh(interval=10000, key="agenda_refresh")
 
    # Simpan jumlah anggota terakhir yang pernah dilihat
    if "last_seen_members" not in st.session_state:
        st.session_state.last_seen_members = n_members
 
    new_members = n_members - st.session_state.last_seen_members
 
    # Notifikasi jika ada anggota baru
    if new_members > 0:
        st.toast(f"🎉 {new_members} anggota baru bergabung!")
        st.markdown(
            f"""
            <div style="
                background:rgba(255,107,53,.1);
                border:1px solid rgba(255,107,53,.3);
                border-radius:12px;
                padding:12px 16px;
                margin-bottom:16px;
                color:#ff6b35;
                font-weight:600;">
                🔄 Ada {new_members} anggota baru. Klik Update untuk memperbarui agenda.
            </div>
            """,
            unsafe_allow_html=True,
        )
 
    # ── Top bar: member count + update button ──
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown(pill(f"👥 {n_members} ANGGOTA"), unsafe_allow_html=True)
    with col_r:
        with st.container():
            st.markdown('<div class="ghost">', unsafe_allow_html=True)
            if st.button("🔄 Update", key="btn_update"):
                fresh = load_session(code)
                if fresh:
                    st.session_state.agenda = build_agenda(fresh)
                st.session_state.last_seen_members = n_members
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
 
    st.markdown(h1("Agenda sesi hari ini"), unsafe_allow_html=True)
    st.markdown(sub("Disusun otomatis dari jawaban semua anggota"), unsafe_allow_html=True)
 
    # ── Session code badge ──
    colors  = theme_colors()
    text    = colors["text"]
    subtext = colors["subtext"]
    card_bg = colors["card_bg"]
    border  = colors["border"]
 
    st.markdown(
        f'''
        <div style="
            background:{card_bg};
            border:1.5px solid {border};
            border-radius:12px;
            padding:12px 18px;
            margin-bottom:20px;
            display:flex;
            justify-content:space-between;
            align-items:center;
        ">
            <span style="color:{subtext};font-size:12px;font-weight:600;letter-spacing:.4px;">
                KODE SESI
            </span>
            <span style="color:#ff6b35;font-size:20px;font-weight:800;letter-spacing:3px;">
                {code.upper()}
            </span>
        </div>
        ''',
        unsafe_allow_html=True,
    )
 
    # ── Prioritas ──
    st.markdown(sec("🔥  Prioritas Pembahasan"), unsafe_allow_html=True)
    for item in (agenda.get("prioritas") or ["—"]):
        colors = theme_colors()
        text   = colors["text"]
        st.markdown(card(
            f'<span style="color:{text};font-size:14px;font-weight:500;">{item}</span>',
            bg="rgba(255,107,53,.07)", border="rgba(255,107,53,.18)"
        ), unsafe_allow_html=True)
 
    kendala = agenda.get("kendala", [])
    if kendala:
        sp(4)
        st.markdown(sec("⚠️  Hal yang Perlu Diperjelas"), unsafe_allow_html=True)
        for item in kendala:
            colors = theme_colors()
            text   = colors["text"]
            st.markdown(card(
                f'<span style="color:{text};font-size:14px;">{item}</span>',
                bg="rgba(255,193,7,.06)", border="rgba(255,193,7,.18)"
            ), unsafe_allow_html=True)
 
    sp(4)
    st.markdown(sec("⏱️  Saran Alur Sesi"), unsafe_allow_html=True)
    alur       = agenda.get("alur", [])
    colors     = theme_colors()
    row_border = colors["border"]
    row_text   = colors["subtext"]
    alur_rows  = "".join([
        f'<div style="display:flex;justify-content:space-between;padding:9px 0;'
        f'border-bottom:1px solid {row_border};font-size:13px;">'
        f'<span style="color:{row_text};">{a["label"]}</span>'
        f'<span style="color:#ff6b35;font-weight:700;">{a["menit"]}m</span></div>'
        for a in alur
    ])
    st.markdown(card(alur_rows, pad="4px 16px"), unsafe_allow_html=True)
 
    roles = agenda.get("roles", {})
    if roles:
        sp(4)
        st.markdown(sec("👤  Saran Peran Anggota"), unsafe_allow_html=True)
        for nama, role in roles.items():
            colors = theme_colors()
            text   = colors["text"]
            st.markdown(card(
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'<span style="font-weight:700;font-size:14px;color:{text};min-width:80px;">{nama}</span>'
                f'{badge(role)}</div>'
            ), unsafe_allow_html=True)
 
    sp(20)
 
    if st.button("▶  Mulai Timer"):
        if alur:
            save_timer(code, {
                "running": True, "paused": False, "alur_index": 0,
                "start_ts": time.time(),
                "remaining_at_start": alur[0]["menit"] * 60,
                "paused_remaining":   alur[0]["menit"] * 60,
            })
        nav("timer")
 
    sp()
    with st.container():
        st.markdown('<div class="ghost">', unsafe_allow_html=True)
        if st.button("← Kembali ke Beranda", key="back_a"): nav("landing")
        st.markdown("</div>", unsafe_allow_html=True)

 
def page_timer():
    import streamlit.components.v1 as components
    from streamlit_autorefresh import st_autorefresh
 
    # Sync every 4 seconds — keeps all devices in sync
    st_autorefresh(interval=4000, limit=None, key="timer_sync")
 
    code   = st.session_state.get("session_code", "")
    agenda = st.session_state.get("agenda", {})
    alur   = agenda.get("alur", [])
 
    # ── Fetch latest from DB (lightweight) ──
    ts, n_members = load_timer_only(code)
 
    if ts:
        idx        = ts.get("alur_index", 0)
        paused     = ts.get("paused", False)
        start_ts   = ts.get("start_ts", time.time())
        rem_start  = ts.get("remaining_at_start", 0)
        paused_rem = ts.get("paused_remaining", 0)
    else:
        idx        = 0
        paused     = False
        start_ts   = time.time()
        rem_start  = alur[0]["menit"] * 60 if alur else 600
        paused_rem = rem_start
 
    # ── Selesai screen ──
    if not alur or idx >= len(alur):
        colors  = theme_colors()
        text    = colors["text"]
        subtext = colors["subtext"]
        st.markdown(f"""
        <div style="text-align:center;padding:60px 0 20px;">
            <div style="font-size:56px;margin-bottom:16px;">🎉</div>
            <h1 style="font-size:26px;font-weight:800;color:{text};">Sesi Selesai!</h1>
            <p style="color:{subtext};font-size:14px;margin-top:8px;">Kerja bagus semuanya!</p>
        </div>""", unsafe_allow_html=True)
        if st.button("← Kembali ke Agenda"): nav("agenda")
        return
 
    current   = alur[idx]
    total_sec = current["menit"] * 60
    remaining = paused_rem if paused else max(0, int(rem_start - (time.time() - start_ts)))
    progress  = 1.0 - (remaining / total_sec) if total_sec else 1.0
 
    # ── Header ──
    st.markdown(pill(f"👥  {n_members} ANGGOTA"), unsafe_allow_html=True)
    st.markdown(h1("Agenda sesi hari ini"), unsafe_allow_html=True)
    st.markdown(sub("Disusun otomatis dari jawaban semua anggota"), unsafe_allow_html=True)
 
    # ── Alur list with active highlight ──
    colors     = theme_colors()
    card_bg    = colors["card_bg"]
    row_border = colors["border"]
    subtext    = colors["subtext"]
 
    alur_rows = ""
    for i, a in enumerate(alur):
        if   i < idx:  c, w, pre = subtext,    "500", "✓"
        elif i == idx: c, w, pre = colors["text"], "700", "▶"
        else:          c, w, pre = subtext,    "400", "○"
        alur_rows += (
            f'<div style="display:flex;justify-content:space-between;padding:10px 0;'
            f'border-bottom:1px solid {row_border};font-size:13px;">'
            f'<span style="color:{c};font-weight:{w};">{pre}  {a["label"]}</span>'
            f'<span style="color:{"#ff6b35" if i==idx else c};font-weight:700;">{a["menit"]}m</span></div>'
        )
    st.markdown(card(alur_rows, pad="4px 16px"), unsafe_allow_html=True)
    sp(8)
 
    # ── JS countdown timer ──
    colors  = theme_colors()
    text    = colors["text"]
    subtext = colors["subtext"]
    mins_d, secs_d = remaining // 60, remaining % 60
    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@800&display=swap" rel="stylesheet">
    <div style="text-align:center;padding:28px 24px;background:rgba(255,107,53,.07);
         border:1.5px solid rgba(255,107,53,.22);border-radius:16px;">
        <div style="font-size:11px;font-weight:700;color:#ff6b35;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">{current['label']}</div>
        <div id="t" style="font-size:68px;font-weight:800;color:{text};font-family:'Plus Jakarta Sans',sans-serif;
             letter-spacing:-3px;line-height:1;font-variant-numeric:tabular-nums;">{mins_d:02d}:{secs_d:02d}</div>
        <div id="st" style="font-size:12px;color:{subtext};margin-top:10px;">{"⏸  Dijeda" if paused else "▶  Berjalan"}</div>
    </div>
    <script>
        var rem={remaining}, paused={'true' if paused else 'false'};
        function fmt(n){{return String(Math.floor(n/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');}}
        document.getElementById('t').textContent=fmt(rem);
        if(!paused && rem>0){{var iv=setInterval(function(){{
            if(rem>0){{rem--;document.getElementById('t').textContent=fmt(rem);}}
            else{{clearInterval(iv);document.getElementById('st').textContent='⏰ Waktu habis';}}
        }},1000);}}
    </script>
    """, height=175)
 
    st.progress(min(progress, 1.0))
    sp(16)
 
    # ── Controls ──
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown('<div class="ghost">', unsafe_allow_html=True)
            if st.button("▶  Lanjutkan" if paused else "⏸  Pause", key="btn_pause"):
                if paused:
                    save_timer(code, {**(ts or {}), "paused": False,
                                      "start_ts": time.time(), "remaining_at_start": paused_rem})
                else:
                    save_timer(code, {**(ts or {}), "paused": True, "paused_remaining": remaining})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        is_last = idx >= len(alur) - 1
        if st.button("Selesai ✓" if is_last else "Next →", key="btn_next"):
            nxt = idx + 1
            if nxt < len(alur):
                save_timer(code, {
                    "running": True, "paused": False, "alur_index": nxt,
                    "start_ts": time.time(),
                    "remaining_at_start": alur[nxt]["menit"] * 60,
                    "paused_remaining":   alur[nxt]["menit"] * 60,
                })
            else:
                save_timer(code, {"running": False, "paused": False, "alur_index": nxt,
                                  "start_ts": time.time(), "remaining_at_start": 0, "paused_remaining": 0})
            st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.markdown(get_css(), unsafe_allow_html=True)

    # ── Theme Toggle ─────────────────────────────────────────
    top1, top2 = st.columns([4,1])

    with top2:

        icon = (
            "☀️"
            if st.session_state.theme == "dark"
            else "🌙"
        )

        if st.button(icon, key="theme_toggle"):
            toggle_theme()
            st.rerun()
    init_from_url()
    {
        "landing":     page_landing,
        "buat_step1":  page_buat_step1,
        "buat_step2":  page_buat_step2,
        "gabung":      page_gabung,
        "gabung_form": page_gabung_form,
        "agenda":      page_agenda,
        "timer":       page_timer,
    }.get(st.session_state.get("page", "landing"), page_landing)()

main()