import os
import re

dir_path = "/home/deck/Desktop/huntarr.io-archive-main/.github/workflows"

replacements = {
    r"uses: actions/checkout@v4": "uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2",
    r"uses: actions/checkout@v3": "uses: actions/checkout@8f4b7f84864484a7bf31766abe9204da3cbe65b3  # v3.5.0",
    r"uses: docker/setup-qemu-action@v3": "uses: docker/setup-qemu-action@4574d27a4764455b42196d70a065bc6853246a25  # v3.4.0",
    r"uses: docker/setup-buildx-action@v3": "uses: docker/setup-buildx-action@f95db51fddba0c2d1ec667646a06c2ce06100226  # v3.0.0",
    r"uses: docker/login-action@v3": "uses: docker/login-action@343f7c4344506bcbf9b4de18042ae17996df046d  # v3.0.0",
    r"uses: docker/build-push-action@v5": "uses: docker/build-push-action@4a13e500e55bc31b3a14a6e601bfab3b10b0e5cc  # v5.1.0",
    r"uses: actions/setup-python@v5": "uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0",
    r"uses: actions/setup-python@v4": "uses: actions/setup-python@65d7f2d534ac1bc67fcd62888c5f4f3d2cb2b236  # v4.7.1",
    r"uses: actions/upload-artifact@v4": "uses: actions/upload-artifact@5d5d22a31266ced268874388b861e4b58bb5c2f3  # v4.3.1",
    r"uses: actions/upload-artifact@v3": "uses: actions/upload-artifact@a8a3f3ad30e3422c9c204c3dd27ed1477dfc89f5  # v3",
    r"uses: actions/download-artifact@v4": "uses: actions/download-artifact@c850b930e6ba138125429b7e5c93fc707cb86dac  # v4.1.4",
    r"uses: actions/download-artifact@v3": "uses: actions/download-artifact@9bc31d5cb31d48cad25145ad17f1177af00b1a03  # v3",
    r"uses: softprops/action-gh-release@v1": "uses: softprops/action-gh-release@9d7c94cfd0a1f3ed45544c887983e9fa900f0564  # v1",
}

for filename in os.listdir(dir_path):
    if filename.endswith(".yml"):
        filepath = os.path.join(dir_path, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        for old, new in replacements.items():
            content = re.sub(old + r"(?!\.)", new, content)
            
        with open(filepath, 'w') as f:
            f.write(content)
            
print("Done")
