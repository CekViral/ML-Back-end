# Ganti sel konversi TFLite Anda dengan kode ini di notebook
# [Capstone]_IndoBERT_Fine_Tuning.ipynb

import tensorflow as tf

# Pastikan variabel ini sesuai dengan nama folder SavedModel Anda
saved_model_dir = "D:\College\Coding_Camp_2025\capstone_project\cekviral_project\models\indobert_savedmodel" 
MAX_SEQUENCE_LENGTH = 128

# 1. Muat SavedModel yang sudah ada
loaded_model = tf.saved_model.load(saved_model_dir)

# 2. Dapatkan 'signature' default dari model
# Ini adalah cara model mengharapkan input
infer = loaded_model.signatures['serving_default']

# 3. Buat 'concrete function' dengan bentuk input yang kita inginkan secara eksplisit
# Ini adalah langkah kunci. Kita memaksa input harus berbentuk (1, 128)
# Sesuai dengan data yang dikirim oleh tokenizer Anda.
@tf.function(
    input_signature=[
        tf.TensorSpec(shape=[1, MAX_SEQUENCE_LENGTH], dtype=tf.int32, name='input_ids'),
        tf.TensorSpec(shape=[1, MAX_SEQUENCE_LENGTH], dtype=tf.int32, name='attention_mask'),
        tf.TensorSpec(shape=[1, MAX_SEQUENCE_LENGTH], dtype=tf.int32, name='token_type_ids'),
    ]
)
def serving_fn(input_ids, attention_mask, token_type_ids):
    # Panggil fungsi inferensi asli dengan input yang sudah dibungkus dictionary
    return infer(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)

# Dapatkan concrete function yang sudah kita definisikan
concrete_func = serving_fn.get_concrete_function()

# 4. Buat konverter DARI CONCRETE FUNCTION, bukan dari saved_model lagi
converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])

# 5. Aktifkan opsi ini untuk memastikan kompatibilitas
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS, # Aktifkan TensorFlow Lite ops.
    tf.lite.OpsSet.SELECT_TF_OPS    # Aktifkan TensorFlow ops untuk kompatibilitas.
]

# 6. (Opsional tapi direkomendasikan) Tambahkan optimisasi
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# 7. Lakukan proses konversi
tflite_model = converter.convert()

# 8. Simpan model TFLite yang sudah diperbaiki
tflite_model_path = "D:\College\Coding_Camp_2025\capstone_project\cekviral_project\indobert_model.tflite"
with open(tflite_model_path, "wb") as f:
    f.write(tflite_model)

print(f"Model TFLite yang sudah diperbaiki berhasil dibuat di: {tflite_model_path}")
print("Silakan ganti nama file ini menjadi 'indobert_model.tflite' dan letakkan di folder 'models/' proyek Anda.")