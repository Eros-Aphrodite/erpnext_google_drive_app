from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = [ln.strip() for ln in f.read().splitlines() if ln.strip() and not ln.startswith("#")]

setup(
    name="erpnext_google_drive_app",
    version="0.1.0",
    description="ERPNext Google Drive Integration (Frappe app)",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
)

