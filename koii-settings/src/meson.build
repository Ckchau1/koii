# Configure the main executable
configure_file(
  input: 'koii-settings.in',
  output: 'koii-settings',
  configuration: conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)

# Install Python modules
python_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'config.py',
  'backend.py',
  'keyring.py',
]

install_data(python_sources,
  install_dir: pythondir / 'koii_settings'
)

# Install pages
install_subdir('pages',
  install_dir: pythondir / 'koii_settings'
)

