"""Fungsi bersama: lokasi berkas, parser dump MySQL, normalisasi teks Arab & Indonesia."""
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
BUILD = os.path.join(ROOT, "build")
DB_PATH = os.path.join(BUILD, "teman-hadits.sqlite")

# ---------------------------------------------------------------------------
# Daftar kitab. id = kunci tetap yang dipakai di URL situs (/hadits/bukhari/1).
# lidwa = nama berkas di sumber carihadis/Lidwa, fawaz = nama edisi fawazahmed0.
# ---------------------------------------------------------------------------
KITAB = [
    # id,        nama Indonesia,             nama Arab,                 penyusun,                         wafat (H), lidwa berkas,                 fawaz
    ("bukhari",  "Shahih al-Bukhari",        "صحيح البخاري",            "Muhammad bin Isma'il al-Bukhari", 256, "shahih-bukhari.sql",          "bukhari"),
    ("muslim",   "Shahih Muslim",            "صحيح مسلم",               "Muslim bin al-Hajjaj",            261, "shahih-muslim.sql",           "muslim"),
    ("abudawud", "Sunan Abu Dawud",          "سنن أبي داود",            "Abu Dawud as-Sijistani",          275, "sunan-abu-daud.sql",          "abudawud"),
    ("tirmidzi", "Jami' at-Tirmidzi",        "جامع الترمذي",            "Abu 'Isa at-Tirmidzi",            279, "sunan-tirmidzi.sql",          "tirmidhi"),
    ("nasai",    "Sunan an-Nasa'i",          "سنن النسائي",             "Ahmad bin Syu'aib an-Nasa'i",     303, "sunan-nasai.sql",             "nasai"),
    ("ibnumajah","Sunan Ibnu Majah",         "سنن ابن ماجه",            "Muhammad bin Yazid Ibnu Majah",   273, "sunan-ibnu-majah.sql",        "ibnmajah"),
    ("malik",    "Al-Muwaththa' (riwayat Yahya al-Laitsi)", "موطأ مالك", "Malik bin Anas",                  179, "muwatho_malik.sql",           "malik"),
    ("ahmad",    "Musnad Ahmad",             "مسند أحمد",               "Ahmad bin Hanbal",                241, "musnad-ahmad.sql",            None),
    ("darimi",   "Sunan ad-Darimi",          "سنن الدارمي",             "'Abdullah bin 'Abdurrahman ad-Darimi", 255, "musnad_darimi.sql",      None),
    ("syafii",   "Musnad asy-Syafi'i",       "مسند الشافعي",            "Muhammad bin Idris asy-Syafi'i",  204, "musnad-syafii.sql",           None),
]
# Riyadhus Shalihin tidak dimuat sebagai riwayat: baris sumbernya per-bab / per-halaman,
# bukan per-hadits (lihat docs/01-audit-data.md). Ia masuk karantina sampai disegmentasi ulang.
KARANTINA_BERKAS = ["riyadhus-shalihin.sql", "riyadhus-shalihin-arab.sql"]


# ---------------------------------------------------------------------------
# Parser dump phpMyAdmin (INSERT ... VALUES (...),(...);)
# ---------------------------------------------------------------------------
_ROW = re.compile(r"\((\d+),\s*'((?:[^'\\]|\\.)*)',\s*'((?:[^'\\]|\\.)*)',\s*'((?:[^'\\]|\\.)*)'\)", re.S)
_ESC = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "Z": "\x1a"}
_UNESC = re.compile(r"\\(.)", re.S)


def _unescape(s):
    return _UNESC.sub(lambda m: _ESC.get(m.group(1), m.group(1)), s)


def read_mysql_dump(path):
    """Hasilkan (id, kitab, arab, terjemah) dari dump bertabel 4 kolom."""
    text = open(path, encoding="utf8").read()
    for m in _ROW.finditer(text):
        yield int(m.group(1)), _unescape(m.group(2)), _unescape(m.group(3)), _unescape(m.group(4))


# ---------------------------------------------------------------------------
# Normalisasi Arab
# ---------------------------------------------------------------------------
HARAKAT = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")  # harakat, tanwin, syaddah, tatwil
_ALIF = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": ""})
_NON_AR = re.compile(r"[^ء-ي\s]")
_WS = re.compile(r"\s+")


def strip_harakat(s):
    return HARAKAT.sub("", s)


def norm_ar(s):
    """Teks Arab -> bentuk polos untuk pencarian/pencocokan (tanpa harakat, hamzah diseragamkan)."""
    s = unicodedata.normalize("NFC", s or "")
    s = strip_harakat(s)
    s = s.translate(_ALIF)
    s = _NON_AR.sub(" ", s)
    return _WS.sub(" ", s).strip()


def norm_id(s):
    """Teks Indonesia -> huruf kecil tanpa tanda baca, untuk pencarian."""
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[`'’‘]", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return _WS.sub(" ", s).strip()


# ---------------------------------------------------------------------------
# Rantai perawi dari terjemahan Lidwa: nama perawi ditulis dalam [kurung siku].
# ---------------------------------------------------------------------------
_BRACKET = re.compile(r"\[([^\[\]]{2,80})\]")


def rantai_dari_terjemah(t):
    return [n.strip() for n in _BRACKET.findall(t or "")]


def clean_html(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&quot;", '"').replace("&amp;", "&")
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()


# ---------------------------------------------------------------------------
# Pemotong awalan ringan (light stemming) untuk pencarian Arab.
# "والخنزير" -> "خنزير", "بالنيات" -> "نيات". Hanya proklitik; akar kata tidak diubah
# supaya hasil pencarian tetap bisa dijelaskan ke pengguna.
# ---------------------------------------------------------------------------
_PROKLITIK = ("وبال", "وكال", "فبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل")


def stem_ar(word):
    for p in _PROKLITIK:
        if word.startswith(p) and len(word) - len(p) >= 3:
            return word[len(p):]
    return word


def akar_ar(normalized_text):
    return " ".join(stem_ar(w) for w in normalized_text.split())
