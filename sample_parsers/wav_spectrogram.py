import numpy as np
import math
import io
import wave
import matplotlib.pyplot as plt

def np_spectrogram(s, nfft, length, shift):
    S = [np.fft.fft(s[n:n + length], n=nfft) for n in range(0, s.size - length + shift, shift)]
    S = np.abs(np.asarray(S).T[:nfft // 2, :].astype(np.complex64))
    S_norm = (S - np.mean(S)) / np.std(S)

    return S_norm


class ParserImpl(Parser):
    def process_sample(self, sample):
        pass

    def process_experiment(self, experiment):
        nfft = 64
        length = 480 # 30 ms
        shift = length

        self.print_text("Spectrogram params: nfft=%i, length=%i, shift=%i" % (nfft, length, shift))

        for s in experiment["samples"]:
            # 0. Read sample date

            with wave.open("input/%s/%s" % (experiment["uid"], s["file"])) as f:

                # 1.1. Calc WAV length in seconds

                num_samples = f.getnframes()
                sample_rate = f.getframerate()

                # 1.2. Print WAV length in seconds

                self.print_text("WAV (%s) length: %f s\n\r" % (s["uid"], num_samples / sample_rate))

                # 2. Read audio samples

                samples = np.frombuffer(f.readframes(num_samples), dtype=np.int16)

                # 3. Compute spectrogram

                s = np_spectrogram(samples, nfft, length, shift)

                # 4. Output spectrogram

                plt.figure()
                plt.pcolormesh(np.squeeze(s))
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                self.print_image(buf.read())
                buf.close()

    def process_batch(self, batch):
        pass
