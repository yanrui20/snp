import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import platform

class SNP:
    def __init__(self, filepath, filetype, n):
        self.filepath = filepath
        self.filetype = filetype.upper()
        self.n = n
        self.filename = self.filename_process()
        self.data = self.get_data()
    
    def filename_process(self):
        filename = self.filepath
        system = platform.system().lower()
        if system == "windows":
            filename = filename.split("\\")[-1]
        else:
            filename = filename.split("/")[-1]
        return filename

    def get_data(self):
        if self.filetype == "DB":
            return self.process_DB_file()
        elif self.filetype == "MA":
            return self.process_MA_file()
        else:
            raise ValueError("Unknown File Type")
    
    def process_DB_file(self):
        with open(self.filepath, "r") as f:
            lines = f.readlines()
        
        header = lines[5][1:] + lines[6][1:] + lines[7][1:]
        header = header.split()

        lines = lines[8:]
        pre_data = [(lines[i*3] + lines[i*3+1] + lines[i*3+2]).split() for i in range(len(lines // self.n))]
        pre_data = pd.DataFrame(data=pre_data, columns=header).astype(float)

        ## change to MA
        data = pd.DataFrame()
        data["freq[MHz]"] = pre_data["Freq"] * 1e3  ## GHz -> MHz
        pairs = [f"S{i}{j}" for i in range(1, self.n+1) for j in range(1, self.n+1)]
        
        for pair in pairs:
            data[f"re:{pair}"] = pre_data[f"DB{pair}"] * np.cos(pre_data[f"Ang{pair}"])
            data[f"im:{pair}"] = pre_data[f"DB{pair}"] * np.sin(pre_data[f"Ang{pair}"])

        return self.expand_MA_data(data)

    def process_MA_file(self):
        with open(self.filepath, "r") as f:
            lines = f.readlines()

        header = lines[4][1:].strip()
        header = header.split()

        pre_data = [line.split() for line in lines[5:]]

        data = pd.DataFrame(data=pre_data, columns=header).astype(float)
        data["freq[MHz]"] = data["freq[Hz]"] / 1e6
        data.drop(columns=["freq[Hz]"])

        return self.expand_MA_data(data)
    
    def expand_MA_data(self, data):
        pairs = [f"S{i}{j}" for i in range(1, self.n+1) for j in range(1, self.n+1)]
        for pair in pairs:
            data[f"{pair}[MODULUS]"] = np.abs(data[f"re:{pair}"] + 1j * data[f"im:{pair}"])
            data[f"{pair}[DB]"] = 20 * np.log10(data[f"{pair}[MODULUS]"])
            data[f"{pair}[VSWR]"] = (1 + data[f"{pair}[MODULUS]"]) / (1 - data[f"{pair}[MODULUS]"])
        return data

    ## name : smith, db, modulus, vswr. Don't worry about upper and lower case.
    ## pairs : Select which port pairs to draw. You can select multiple port pairs, for example ["S11", "S12", "S21"]
    ## limitMHZ : [minMHZ, maxMHZ], if maxMHZ > the max freq in the data, it is OK
    def draw(self, name, pairs, limitMHZ=[0, 100000]):
        data = self.data.copy()
        data = data[(data["freq[MHz]"] >= limitMHZ[0]) & (data["freq[MHz]"] <= limitMHZ[1])]
        name = name.upper()
        if name == "SMITH":
            plt.figure(figsize=(8, 8), dpi=300)
            plt.xlim(-1, 1)
            plt.ylim(-1, 1)
            plt.xlabel("re")
            plt.ylabel("im")
        else:
            plt.figure(figsize=(12, 5), dpi=300)
            x = data["freq[MHz]"]
            plt.xlabel("freq[MHZ]")
            plt.ylabel(name)
        for pair in pairs:
            if name == "SMITH":
                x = data[f"re:{pair}"]
                y = data[f"im:{pair}"]
            else:
                y = data[f"{pair}[{name}]"]
            plt.plot(x, y, label=pair)
        plt.legend()
        # plt.show() ## you can show the picture if you need
        plt.savefig(f"{self.filename}_{name}_{pairs}_{limitMHZ}.png")


if __name__ == "__main__":
    s2p = SNP(filepath="BSL1.s2p", filetype="ma", n=2)
    # s2p = SNP(filepath=r"D:\xxx\BSL1.s2p", filetype="db", n=2) ## on windows
    s2p.draw(name="smith", pairs=["S11"])
    # s2p.draw(name="vswr", pairs=["S11", "S22"], limitMHZ=[800, 1000])
    # s2p.draw(name="modulus", pairs=["S11", "S22"], limitMHZ=[800, 1000])
    # s2p.draw(name="db", pairs=["S11", "S12", "S22"], limitMHZ=[800, 1000])
