project('koii-settings',
  version: '1.0.0',
  meson_version: '>= 0.59.0',
  default_options: [
    'warning_level=2',
  ],
)

# Python installation
python = import('python')
py_installation = python.find_installation('python3', required: true, modules: ['gi'])
i18n = import('i18n')

# Dependencies
dependency('glib-2.0', version: '>= 2.66')
dependency('gtk4', version: '>= 4.0')
dependency('libadwaita-1', version: '>= 1.0')

# Prefix and directories
prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
pythondir = py_installation.get_install_dir()

# Configuration
conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('VERSION', meson.project_version())
conf.set('PKGDATADIR', pkgdatadir)
conf.set('LOCALEDIR', prefix / get_option('localedir'))
conf.set('GETTEXT_PACKAGE', meson.project_name())

# Subdirectories
subdir('data')
subdir('src')
subdir('po')

# Post-install scripts
gnome = import('gnome')
gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
