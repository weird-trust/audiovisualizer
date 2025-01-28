from scipy.io import wavfile
import numpy as np
import json

def process_audio(file_path, output_path, window_size=1024, reduction_factor=32):
    # Lade die WAV-Datei
    sample_rate, samples = wavfile.read(file_path)

    # Anzahl der Fenster
    num_windows = len(samples) // window_size

    # Liste zum Speichern der Frequenzdaten
    frequency_data = []

    # Frequenzdaten extrahieren und reduzieren
    for i in range(num_windows):
        window = samples[i * window_size:(i + 1) * window_size]
        fft_result = np.fft.fft(window)
        magnitudes = np.abs(fft_result[:window_size // 2])

        # Reduziere die Datenmenge durch Averaging
        reduced_magnitudes = []
        for j in range(0, len(magnitudes), reduction_factor):
            group = magnitudes[j:j + reduction_factor]
            average = np.mean(group)
            reduced_magnitudes.append(average)

        frequency_data.append(reduced_magnitudes)

    # Speichern der reduzierten Frequenzdaten in einer JSON-Datei
    with open(output_path, "w") as f:
        json.dump(frequency_data, f)

    print(f"Reduced frequency data saved to {output_path}")

# Beispielaufruf des Skripts
process_audio("public/audio/output.wav", "frequency_data.json")
