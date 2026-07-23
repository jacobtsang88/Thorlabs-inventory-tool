# plotter.py
try:
    import matplotlib.pyplot as plt
except ImportError: 
    plt = None


class Plotter:

    def plot(self, curve_or_series, title="", output_path=None, show=True):
        if plt is None:
            raise ImportError("matplotlib is required to plot spectra")

        if isinstance(curve_or_series, dict):
            series = [(title or "Series", curve_or_series)]
        else:
            series = curve_or_series

        plt.figure(figsize=(9, 5))

        for label, curve in series:
            # Sort wavelengths numerically
            x = sorted(curve.keys(), key=float)
            y = [curve[i] for i in x]
            plt.plot(x, y, label=label)

        if title:
            plt.title(title)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("%")
        plt.grid(True, linestyle="--", alpha=0.5)

        # Uncomment legend so you can see labels when plotting multiple series
        if len(series) > 0:
            plt.legend(loc="best")

        if output_path:
            output_path = str(output_path)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")

        if show:
            plt.show()

        plt.close()


'''
try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - defensive
    plt = None


class Plotter:

    def plot(self, curve_or_series, title="", output_path=None, show=True):
        if plt is None:
            raise ImportError("matplotlib is required to plot spectra")

        if isinstance(curve_or_series, dict):
            series = [(title or "Series", curve_or_series)]
        else:
            series = curve_or_series

        for label, curve in series:
            x = sorted(curve.keys(), key=float)
            y = [curve[i] for i in x]
            plt.plot(x, y, label=label)

        if title:
            plt.title(title)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("%")
        
        if output_path:
            output_path = str(output_path)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")

        if show:
            plt.show()

        plt.close()

'''