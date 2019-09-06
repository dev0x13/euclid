import numpy as np
import matplotlib.pyplot as plt
import io

class ParserImpl(Parser):
    def process_sample(self, sample):
        # 1. Read raw data
        with open("input/%s" % sample["file"], "rb") as f:
            data = np.frombuffer(f.read(), dtype=np.int16)

        # 2. Reshape raw data
        data = np.reshape(data, (161, 512))

        # 3. Remove defected sampes
        data = data[..., 20:]

        # 4. Transpose data
        data = np.transpose(data)

        # 5. Output grayscale image
        plt.figure()
        plt.gray()
        plt.pcolormesh(data)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        self.print_image(buf.read())
        buf.close()

    def process_experiment(self, experiment):
        pass

    def process_batch(self, batch):
        pass

