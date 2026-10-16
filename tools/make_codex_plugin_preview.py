"""Create a directory preview from labelled synthetic validation outputs, never private observations."""
from pathlib import Path
import argparse
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("validation_run", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error("Output already exists; use a new name")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "plugins" / "codex-ael" / "runtime"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import tifffile
    from ael.geometry import EclipseGeometry
    from ael.polar import to_polar
    data = np.load(a.validation_run / "synthetic-input" / "linear.npy")
    valid = np.load(a.validation_run / "synthetic-input" / "valid.npy")
    geo = EclipseGeometry.from_json(a.validation_run / "synthetic-input" / "geometry.json")
    structure = tifffile.imread(a.validation_run / "structure" / "structure_mono.tif").astype(float) / 65535
    polar = to_polar(structure[..., 0], geo, center="sun", r_range=(23, 110), n_pa=720, valid=valid)
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor="#10151d")
    fig.text(.055, .92, "AGENTIC ECLIPSE LIBRARY", fontsize=28, weight="bold", color="white")
    fig.text(.055, .866, "From a linear image to structure and polar views", fontsize=19, color="#cbd5e1")
    fig.text(.055, .79, "SYNTHETIC TEST DATA · SOFTWARE DEMONSTRATION", fontsize=13, weight="bold", color="#f2c66d")
    positions = ([.055,.29,.28,.43], [.365,.29,.28,.43], [.675,.29,.27,.43])
    titles = ("1  Linear input", "2  Structure display", "3  Polar view")
    images = (np.log1p(np.maximum(data,0)), structure, np.nan_to_num(polar.display(), nan=0))
    for pos, title, img in zip(positions, titles, images):
        ax=fig.add_axes(pos, facecolor="#10151d")
        ax.imshow(img, cmap="gray", interpolation="nearest", aspect="auto" if title.startswith("3") else "equal")
        ax.set_title(title, color="white", fontsize=16, loc="left", pad=15)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
    fig.text(.055,.20,"Full input canvas preserved · Missing data stays missing",fontsize=17,color="white")
    fig.text(.055,.145,"Numerical processing runs locally. Calibration and scientific checks remain explicit.",fontsize=14,color="#cbd5e1")
    fig.text(.055,.075,"By Pere Guerra Serra  |  Open source · MIT  |  Python required",fontsize=13,color="#f2c66d")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(a.output,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(a.output)


if __name__ == "__main__":
    main()
