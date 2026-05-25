const { flipFuses, FuseVersion, FuseV1Options } = require('@electron/fuses')
const { execSync } = require('child_process')

// Note: these fuses should match those defined in createPackage.js
// Wrapped in try/catch so a failed fuse-flip (e.g. on Windows with Node v24
// or when the binary is locked) never aborts the npm install.
flipFuses(require('electron'), {
  version: FuseVersion.V1,
  [FuseV1Options.GrantFileProtocolExtraPrivileges]: false
})
  .then(() => {
    // macOS ARM always requires a valid code signature
    if (process.platform === 'darwin' && process.arch === 'arm64') {
      execSync('codesign -s - -a arm64 -f --deep ' + require('electron'))
    }
  })
  .catch((err) => {
    // Non-fatal: fuse flipping can fail when the binary is read-only,
    // already patched, or running under Node v24 on Windows.
    console.warn('[setupDevEnv] flipFuses skipped:', err.message)
  })
