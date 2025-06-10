# cekviral_project/app/services/ml_model.py
import os
import re
import string
import logging
import time

# Import library NLTK, TensorFlow, dan Transformers
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import tensorflow as tf
import numpy as np
from transformers import BertTokenizer

logger = logging.getLogger(__name__)

# Placeholder untuk model dan tokenizer
global_model = None
global_tokenizer = None

# --- KAMUS SLANGWORDS ---
slangwords = {"@": "di", "abis": "habis", "wtb": "beli", "masi": "masih", "wts": "jual", "wtt": "tukar", "bgt": "banget", "maks": "maksimal",
              "plisss": "tolong", "bgttt": "banget", "indo": "indonesia", "bgtt": "banget", "ad": "ada", "rv": "redvelvet", "plis": "tolong",
              "pls": "tolong", "cr": "sumber", "cod": "bayar ditempat", "adlh": "adalah", "afaik": "as far as i know", "ahaha": "haha", "aj": "saja",
              "ajep-ajep": "dunia gemerlap", "ak": "saya", "akika": "aku", "akkoh": "aku", "akuwh": "aku", "alay": "norak", "alow": "halo", "ambilin": "ambilkan",
              "ancur": "hancur", "anjrit": "anjing", "anter": "antar", "ap2": "apa-apa", "apasih": "apa sih", "apes": "sial", "aps": "apa", "aq": "saya",
              "aquwh": "aku", "asbun": "asal bunyi", "aseekk": "asyik", "asekk": "asyik", "asem": "asam", "aspal": "asli tetapi palsu", "astul": "asal tulis",
              "ato": "atau", "au ah": "tidak mau tahu", "awak": "saya", "ay": "sayang", "ayank": "sayang", "b4": "sebelum", "bakalan": "akan", "bandes": "bantuan desa",
              "bangedh": "banget", "banpol": "bantuan polisi", "banpur": "bantuan tempur", "basbang": "basi", "bcanda": "bercanda", "bdg": "bandung", "begajulan": "nakal",
              "beliin": "belikan", "bencong": "banci", "bentar": "sebentar", "ber3": "bertiga", "beresin": "membereskan", "bete": "bosan", "beud": "banget", "bg": "abang",
              "bgmn": "bagaimana", "bgt": "banget", "bijimane": "bagaimana", "bintal": "bimbingan mental", "bkl": "akan", "bknnya": "bukannya", "blegug": "bodoh", "blh": "boleh",
              "bln": "bulan", "blum": "belum", "bnci": "benci", "bnran": "yang benar", "bodor": "lucu", "bokap": "ayah", "boker": "buang air besar", "bokis": "bohong",
              "boljug": "boleh juga", "bonek": "bocah nekat", "boyeh": "boleh", "br": "baru", "brg": "bareng", "bro": "saudara laki-laki", "bru": "baru", "bs": "bisa",
              "bsen": "bosan", "bt": "buat", "btw": "ngomong-ngomong", "buaya": "tidak setia", "bubbu": "tidur", "bubu": "tidur", "bumil": "ibu hamil", "bw": "bawa",
              "bwt": "buat", "byk": "banyak", "byrin": "bayarkan", "cabal": "sabar", "cadas": "keren", "calo": "makelar", "can": "belum", "capcus": "pergi",
              "caper": "cari perhatian", "ce": "cewek", "cekal": "cegah tangkal", "cemen": "penakut", "cengengesan": "tertawa", "cepet": "cepat", "cew": "cewek", "chuyunk": "sayang",
              "cimeng": "ganja", "cipika cipiki": "cium pipi kanan cium pipi kiri", "ciyh": "sih", "ckepp": "cakep", "ckp": "cakep", "cmiiw": "correct me if i'm wrong",
              "cmpur": "campur", "cong": "banci", "conlok": "cinta lokasi", "cowwyy": "maaf", "cp": "siapa", "cpe": "capek", "cppe": "capek", "cucok": "cocok",
              "cuex": "cuek", "cumi": "Cuma miscall", "cups": "culun", "curanmor": "pencurian kendaraan bermotor", "curcol": "curahan hati colongan", "cwek": "cewek",
              "cyin": "cinta", "d": "di", "dah": "deh", "dapet": "dapat", "de": "adik", "dek": "adik", "demen": "suka", "deyh": "deh", "dgn": "dengan", "diancurin": "dihancurkan",
              "dimaafin": "dimaafkan", "dimintak": "diminta", "disono": "di sana", "dket": "dekat", "dkk": "dan kawan-kawan", "dlu": "dulu", "dngn": "dengan", "dodol": "bodoh",
              "doku": "uang", "dongs": "dong", "dpt": "dapat", "dri": "dari", "drmn": "darimana", "drtd": "dari tadi", "dst": "dan seterusnya", "dtg": "datang", "duh": "aduh",
              "duren": "durian", "ed": "edisi", "egp": "emang gue pikirin", "eke": "aku", "elu": "kamu", "emangnya": "memangnya", "emng": "memang", "endak": "tidak", "enggak": "tidak",
              "envy": "iri", "ex": "mantan", "fax": "facsimile", "fifo": "first in first out", "folbek": "follow back", "fyi": "sebagai informasi", "gaada": "tidak ada uang",
              "gag": "tidak", "gaje": "tidak jelas", "gak papa": "tidak apa-apa", "gan": "juragan", "gaptek": "gagap teknologi", "gatek": "gagap teknologi", "gawe": "kerja",
              "gbs": "tidak bisa", "gebetan": "orang yang disuka", "geje": "tidak jelas", "gepeng": "gelandangan dan pengemis", "ghiy": "lagi", "gile": "gila", "gimana": "bagaimana",
              "gino": "gigi nongol", "githu": "gitu", "gj": "tidak jelas", "gmana": "bagaimana", "gn": "begini", "goblok": "bodoh", "golput": "golongan putih", "gowes": "mengayuh sepeda",
              "gpny": "tidak punya", "gr": "gede rasa", "gretongan": "gratisan", "gtau": "tidak tahu", "gua": "saya", "guoblok": "goblok", "gw": "saya", "ha": "tertawa", "haha": "tertawa",
              "hallow": "halo", "hankam": "pertahanan dan keamanan", "hehe": "he", "helo": "halo", "hey": "hai", "hlm": "halaman", "hny": "hanya", "hoax": "isu bohong", "hr": "hari",
              "hrus": "harus", "hubdar": "perhubungan darat", "huff": "mengeluh", "hum": "rumah", "humz": "rumah", "ilang": "hilang", "ilfil": "tidak suka", "imho": "in my humble opinion",
              "imoetz": "imut", "item": "hitam", "itungan": "hitungan", "iye": "iya", "ja": "saja", "jadiin": "jadi", "jaim": "jaga image", "jayus": "tidak lucu", "jdi": "jadi", "jem": "jam",
              "jga": "juga", "jgnkan": "jangankan", "jir": "anjing", "jln": "jalan", "jomblo": "tidak punya pacar", "jubir": "juru bicara", "jutek": "galak", "k": "ke", "kab": "kabupaten",
              "kabor": "kabur", "kacrut": "kacau", "kadiv": "kepala divisi", "kagak": "tidak", "kalo": "kalau", "kampret": "sialan", "kamtibmas": "keamanan dan ketertiban masyarakat",
              "kamuwh": "kamu", "kanwil": "kantor wilayah", "karna": "karena", "kasubbag": "kepala subbagian", "katrok": "kampungan", "kayanya": "kayaknya", "kbr": "kabar", "kdu": "harus",
              "kec": "kecamatan", "kejurnas": "kejuaraan nasional", "kekeuh": "keras kepala", "kel": "kelurahan", "kemaren": "kemarin", "kepengen": "mau", "kepingin": "mau",
              "kepsek": "kepala sekolah", "kesbang": "kesatuan bangsa", "kesra": "kesejahteraan rakyat", "ketrima": "diterima", "kgiatan": "kegiatan", "kibul": "bohong", "kimpoi": "kawin",
              "kl": "kalau", "klianz": "kalian", "kloter": "kelompok terbang", "klw": "kalau", "km": "kamu", "kmps": "kampus", "kmrn": "kemarin", "knal": "kenal", "knp": "kenapa",
              "kodya": "kota madya", "komdis": "komisi disiplin", "komsov": "komunis sovyet", "kongkow": "kumpul bareng teman-teman", "kopdar": "kopi darat", "korup": "korupsi", "kpn": "kapan",
              "krenz": "keren", "krm": "kirim", "kt": "kita", "ktmu": "ketemu", "ktr": "kantor", "kuper": "kurang pergaulan", "kw": "imitasi", "kyk": "seperti", "la": "lah", "lam": "salam",
              "lamp": "lampiran", "lanud": "landasan udara", "latgab": "latihan gabungan", "lebay": "berlebihan", "leh": "boleh", "lelet": "lambat", "lemot": "lambat", "lgi": "lagi",
              "lgsg": "langsung", "liat": "lihat", "litbang": "penelitian dan pengembangan", "lmyn": "lumayan", "lo": "kamu", "loe": "kamu", "lola": "lambat berfikir", "louph": "cinta",
              "low": "kalau", "lp": "lupa", "luber": "langsung, umum, bebas, dan rahasia", "luchuw": "lucu", "lum": "belum", "luthu": "lucu", "lwn": "lawan", "maacih": "terima kasih",
              "mabal": "bolos", "macem": "macam", "macih": "masih", "maem": "makan", "magabut": "makan gaji buta", "maho": "homo", "mak jang": "kaget", "maksain": "memaksa", "malem": "malam",
              "mam": "makan", "maneh": "kamu", "maniez": "manis", "mao": "mau", "masukin": "masukkan", "melu": "ikut", "mepet": "dekat sekali", "mgu": "minggu", "migas": "minyak dan gas bumi",
              "mikol": "minuman beralkohol", "miras": "minuman keras", "mlah": "malah", "mngkn": "mungkin", "mo": "mau", "mokad": "mati", "moso": "masa", "mpe": "sampai", "msk": "masuk",
              "mslh": "masalah", "mt": "makan teman", "mubes": "musyawarah besar", "mulu": "melulu", "mumpung": "selagi", "munas": "musyawarah nasional", "muntaber": "muntah dan berak",
              "musti": "mesti", "muupz": "maaf", "mw": "now watching", "n": "dan", "nanam": "menanam", "nanya": "bertanya", "napa": "kenapa", "napi": "narapidana",
              "napza": "narkotika, alkohol, psikotropika, dan zat adiktif ", "narkoba": "narkotika, psikotropika, dan obat terlarang", "nasgor": "nasi goreng", "nda": "tidak", "ndiri": "sendiri",
              "ne": "ini", "nekolin": "neokolonialisme", "nembak": "menyatakan cinta", "ngabuburit": "menunggu berbuka puasa", "ngaku": "mengaku", "ngambil": "mengambil", "nganggur": "tidak punya pekerjaan",
              "ngapah": "kenapa", "ngaret": "terlambat", "ngasih": "memberikan", "ngebandel": "berbuat bandel", "ngegosip": "bergosip", "ngeklaim": "mengklaim", "ngeksis": "menjadi eksis", "ngeles": "berkilah",
              "ngelidur": "menggigau", "ngerampok": "merampok", "ngga": "tidak", "ngibul": "berbohong", "ngiler": "mau", "ngiri": "iri", "ngisiin": "mengisikan", "ngmng": "bicara", "ngomong": "bicara",
              "ngubek2": "mencari-cari", "ngurus": "mengurus", "nie": "ini", "nih": "ini", "niyh": "nih", "nmr": "nomor", "nntn": "nonton", "nobar": "nonton bareng", "np": "now playing", "ntar": "nanti",
              "ntn": "nonton", "numpuk": "bertumpuk", "nutupin": "menutupi", "nyari": "mencari", "nyekar": "menyekar", "nyicil": "mencicil", "nyoblos": "mencoblos", "nyokap": "ibu", "ogah": "tidak mau",
              "ol": "online", "ongkir": "ongkos kirim", "oot": "out of topic", "org2": "orang-orang", "ortu": "orang tua", "otda": "otonomi daerah", "otw": "on the way, sedang di jalan", "pacal": "pacar",
              "pake": "pakai", "pala": "kepala", "pansus": "panitia khusus", "parpol": "partai politik", "pasutri": "pasangan suami istri", "pd": "pada", "pede": "percaya diri", "pelatnas": "pemusatan latihan nasional",
              "pemda": "pemerintah daerah", "pemkot": "pemerintah kota", "pemred": "pemimpin redaksi", "penjas": "pendidikan jasmani", "perda": "peraturan daerah", "perhatiin": "perhatikan", "pesenan": "pesanan",
              "pgang": "pegang", "pi": "tapi", "pilkada": "pemilihan kepala daerah", "pisan": "sangat", "pk": "penjahat kelamin", "plg": "paling", "pmrnth": "pemerintah", "polantas": "polisi lalu lintas",
              "ponpes": "pondok pesantren", "pp": "pulang pergi", "prg": "pergi", "prnh": "pernah", "psen": "pesan", "pst": "pasti", "pswt": "pesawat", "pw": "posisi nyaman", "qmu": "kamu", "rakor": "rapat koordinasi",
              "ranmor": "kendaraan bermotor", "re": "reply", "ref": "referensi", "rehab": "rehabilitasi", "rempong": "sulit", "repp": "balas", "restik": "reserse narkotika", "rhs": "rahasia", "rmh": "rumah"}

# --- AKHIR KAMUS SLANGWORDS ---


# --- FUNGSI PREPROCESSING TEKS ---
def cleaningText(text):
    text = re.sub(r'@[A-Za-z0-9_]+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ') # Menangani newline dan tab
    text = re.sub(r'([,.!?()"])', r' \1 ', text)
    text = re.sub(r'([a-zA-Z]+)[\"()_-]([a-zA-Z]+)', r'\1 \2', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\b(\w*[^aeiou\s])(nya|nua|neo)\b', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text).strip() # Menangani spasi berlebih dan spasi awal/akhir
    return text

def casefoldingText(text):
    text = text.lower()
    return text

def tokenizingText(text):
    text = word_tokenize(text)
    return text

def filteringText(text):
    listStopwords = set(stopwords.words('indonesian'))
    listStopwords1 = set(stopwords.words('english'))
    listStopwords.update(listStopwords1)
    listStopwords.update(['iya','yaa','gak','nya','na','sih','ku',"di","ga","ya","gaa","loh","kah","woi","woii","woy", "yg"])
    filtered = []
    for txt in text:
        if txt not in listStopwords:
            filtered.append(txt)
    text = filtered
    return text

def toSentence(list_words):
    sentence = ' '.join(word for word in list_words)
    return sentence

def fix_slangwords(text):
    words = text.split()
    fixed_words = []
    for word in words:
        if word.lower() in slangwords:
            fixed_words.append(slangwords[word.lower()])
        else:
            fixed_words.append(word)
    fixed_text = ' '.join(fixed_words)
    return fixed_text

def preprocess_text_for_ml(text: str) -> str:
    """
    Menggabungkan semua langkah pra-pemrosesan teks ke dalam satu pipeline,
    termasuk penanganan karakter baris baru dan spasi berlebihan secara otomatis.
    """
    if not isinstance(text, str):
        logger.warning(f"Input to preprocess_text_for_ml is not a string: {type(text)}. Attempting conversion.")
        text = str(text)

    # Ini adalah langkah pertama yang kuat untuk menangani newline dan spasi berlebihan.
    # Digunakan di sini dan di cleaningText untuk redundansi jika ada urutan pemanggilan yang berbeda.
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    text = cleaningText(text)
    text = casefoldingText(text)
    text = fix_slangwords(text)
    tokens = tokenizingText(text)
    tokens = filteringText(tokens)
    text = toSentence(tokens)
    return text
# --- AKHIR FUNGSI PREPROCESSING TEKS ---


# Konfigurasi model dan tokenizer
INDOBERT_TOKENIZER_NAME = "indobenchmark/indobert-lite-base-p2"
MAX_SEQUENCE_LENGTH = 128
FINE_TUNED_MODEL_FILE = "indobert_model.tflite"

# Mapping label untuk klasifikasi biner
CLASS_LABELS = {0: "HOAKS", 1: "FAKTA"}

# Threshold untuk zona "BELUM DIVERIFIKASI" (pada probabilitas kelas FAKTA)
UNCERTAIN_THRESHOLD_LOW = 0.15
UNCERTAIN_THRESHOLD_HIGH = 0.85

def load_ml_model():
    """Memuat model TFLite dan tokenizer-nya."""
    global global_interpreter, global_tokenizer

    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', FINE_TUNED_MODEL_FILE)
    
    try:
        logger.info(f"Memuat model TFLite dari: {model_path}")
        global_interpreter = tf.lite.Interpreter(model_path=model_path)
        global_interpreter.allocate_tensors()
        logger.info("Model TFLite berhasil dimuat.")
        
        logger.info(f"Memuat tokenizer: {INDOBERT_TOKENIZER_NAME}")
        global_tokenizer = BertTokenizer.from_pretrained(INDOBERT_TOKENIZER_NAME)
        logger.info("Tokenizer Hugging Face berhasil dimuat.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan saat memuat model TFLite atau tokenizer: {e}", exc_info=True)
        global_interpreter = None
        global_tokenizer = None


def predict_content_hoax_status(raw_text: str) -> dict:
    """
    Melakukan prediksi menggunakan model TFLite yang sudah dioptimalkan.
    """
    global global_interpreter, global_tokenizer

    if global_interpreter is None or global_tokenizer is None:
        logger.error("Interpreter TFLite atau Tokenizer belum dimuat. Tidak dapat melakukan prediksi.")
        return {
            "status": "error",
            "message": "Model/Tokenizer tidak dimuat.",
            "probabilities": {"HOAKS": 0.0, "FAKTA": 0.0},
            "predicted_label_model": "N/A",
            "highest_confidence": 0.0,
            "final_label_thresholded": "BELUM DIVERIFIKASI",
            "inference_time_ms": 0.0
        }

    start_time = time.perf_counter()
    
    try:
        processed_text = preprocess_text_for_ml(raw_text)
        
        if not processed_text.strip():
            logger.warning("Teks setelah pra-pemrosesan kosong atau hanya spasi.")
            return {
                "status": "error", "message": "Teks setelah pra-pemrosesan kosong.",
                "probabilities": {"HOAKS": 0.0, "FAKTA": 0.0},
                "predicted_label_model": "N/A", "highest_confidence": 0.0,
                "final_label_thresholded": "BELUM DIVERIFIKASI", "inference_time_ms": 0.0
            }

        logger.info(f"Teks setelah pra-pemrosesan: {processed_text[:100]}...")

        encoded_input = global_tokenizer(
            processed_text,
            truncation=True,
            padding='max_length',
            max_length=MAX_SEQUENCE_LENGTH,
            return_tensors='tf'
        )
        
        input_details = global_interpreter.get_input_details()
        output_details = global_interpreter.get_output_details()

        input_ids = tf.cast(encoded_input['input_ids'], dtype=input_details[0]['dtype'])
        attention_mask = tf.cast(encoded_input['attention_mask'], dtype=input_details[1]['dtype'])
        
        global_interpreter.set_tensor(input_details[0]['index'], input_ids)
        global_interpreter.set_tensor(input_details[1]['index'], attention_mask)
        if len(input_details) > 2:
            token_type_ids = tf.cast(encoded_input['token_type_ids'], dtype=input_details[2]['dtype'])
            global_interpreter.set_tensor(input_details[2]['index'], token_type_ids)

        global_interpreter.invoke()
        logits = global_interpreter.get_tensor(output_details[0]['index'])
        
        probabilities_array = tf.nn.softmax(logits, axis=1).numpy()[0]
        
        # Perhatikan CLASS_LABELS: jika key 0 adalah HOAKS, maka prob_hoax adalah probabilities_array[0]
        prob_hoax = float(probabilities_array[0])
        prob_fakta = float(probabilities_array[1])
        predicted_class_index = np.argmax(probabilities_array)
        predicted_label = CLASS_LABELS.get(predicted_class_index, "tidak diketahui")
        
        highest_confidence = float(np.max(probabilities_array))

        final_label_thresholded = "BELUM DIVERIFIKASI"
        if prob_fakta >= UNCERTAIN_THRESHOLD_HIGH:
            final_label_thresholded = "FAKTA"
        elif prob_fakta <= UNCERTAIN_THRESHOLD_LOW:
            final_label_thresholded = "HOAKS"
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"Probabilities: HOAKS={prob_hoax:.4f}, FAKTA={prob_fakta:.4f}")
        logger.info(f"Predicted label by model: {predicted_label}, Final (thresholded): {final_label_thresholded}")
        
        return {
            "status": "success",
            "message": "Prediksi berhasil.",
            "probabilities": {"HOAKS": prob_hoax, "FAKTA": prob_fakta},
            "predicted_label_model": predicted_label,
            "highest_confidence": highest_confidence,
            "final_label_thresholded": final_label_thresholded,
            "inference_time_ms": inference_time_ms
        }

    except Exception as e:
        logger.error(f"Error saat melakukan prediksi: {e}", exc_info=True)
        return {
            "status": "error", "message": f"Kesalahan internal saat prediksi: {str(e)}",
            "probabilities": {"HOAKS": 0.0, "FAKTA": 0.0},
            "predicted_label_model": "N/A", "highest_confidence": 0.0,
            "final_label_thresholded": "BELUM DIVERIFIKASI", "inference_time_ms": 0.0
        }