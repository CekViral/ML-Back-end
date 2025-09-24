import pandas as pd


def transform_to_DataFrame(data):
    """Mengubah data menjadi DataFrame."""
    df = pd.DataFrame(data)
    return df


def transform_status(df):
    """Memisahkan status dari Title ke kolom baru."""
    # Extract status dari Title, baik dalam [ ] atau ( )
    df['Status'] = df['Title'].str.extract(r'[\[\(](.*?)[\]\)]')
    
    # Bersihkan Title dari status
    df['Title'] = df['Title'].str.replace(r'[\[\(].*?[\]\)]\s*', '', regex=True)
    
    return df


def clean_description(text):
    """Membersihkan teks Description tanpa memotong panjang teks."""
    if not text:
        return ''
    # Hapus newline dan carriage return
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Hapus bagian setelah "REFERENSI" jika ada
    ref_index = text.find('REFERENSI')
    if ref_index != -1:
        text = text[:ref_index]
    # Hilangkan spasi ekstra di awal/akhir
    return text.strip()
