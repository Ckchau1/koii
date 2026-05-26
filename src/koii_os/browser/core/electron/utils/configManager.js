const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { app } = require('electron');

class ConfigManager {
  constructor() {
    this.configDir = path.join(app.getPath('userData'), 'koii-configs');
    this.configFile = path.join(this.configDir, 'llm-configs.json');
    this.ensureConfigDirExists();
    this.encryptionKey = this.getOrCreateEncryptionKey();
  }

  ensureConfigDirExists() {
    if (!fs.existsSync(this.configDir)) {
      try {
        fs.mkdirSync(this.configDir, { recursive: true, mode: 0o700 });
        console.log(`Created config directory: ${this.configDir}`);
      } catch (error) {
        console.error(`Failed to create config directory: ${error.message}`);
        throw error;
      }
    }
  }

  getOrCreateEncryptionKey() {
    const keyFile = path.join(this.configDir, '.encryption-key');

    try {
      if (fs.existsSync(keyFile)) {
        return fs.readFileSync(keyFile, 'utf8');
      }

      // Generate a new encryption key (32 bytes for AES-256)
      const newKey = crypto.randomBytes(32).toString('hex');

      // Ensure directory exists before writing
      if (!fs.existsSync(this.configDir)) {
        fs.mkdirSync(this.configDir, { recursive: true, mode: 0o700 });
      }

      fs.writeFileSync(keyFile, newKey, { mode: 0o600 }); // Read/write for owner only
      console.log(`Generated new encryption key at: ${keyFile}`);
      return newKey;
    } catch (error) {
      console.error(`Failed to get/create encryption key: ${error.message}`);
      throw error;
    }
  }

  encrypt(data) {
    const iv = crypto.randomBytes(16);
    const key = Buffer.from(this.encryptionKey, 'hex');
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);

    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');

    return iv.toString('hex') + ':' + encrypted;
  }

  decrypt(encryptedData) {
    const [ivHex, encrypted] = encryptedData.split(':');
    const iv = Buffer.from(ivHex, 'hex');
    const key = Buffer.from(this.encryptionKey, 'hex');
    const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return JSON.parse(decrypted);
  }

  getAllConfigs() {
    try {
      if (!fs.existsSync(this.configFile)) {
        return {};
      }

      const rawData = fs.readFileSync(this.configFile, 'utf8');
      const encryptedData = JSON.parse(rawData);

      const decrypted = {};
      for (const [provider, encrypted] of Object.entries(encryptedData)) {
        try {
          decrypted[provider] = this.decrypt(encrypted);
        } catch (error) {
          console.error(`Failed to decrypt config for ${provider}:`, error);
        }
      }

      return decrypted;
    } catch (error) {
      console.error('Error reading configs:', error);
      return {};
    }
  }

  getConfig(provider) {
    const configs = this.getAllConfigs();
    return configs[provider] || null;
  }

  saveConfig(provider, config) {
    try {
      const allConfigs = this.getAllConfigs();
      const encrypted = this.encrypt(config);
      allConfigs[provider] = encrypted;

      fs.writeFileSync(
        this.configFile,
        JSON.stringify(allConfigs, null, 2),
        { mode: 0o600 } // Restrict file permissions
      );

      console.log(`Saved configuration for ${provider}`);
      return true;
    } catch (error) {
      console.error(`Error saving config for ${provider}:`, error);
      throw error;
    }
  }

  deleteConfig(provider) {
    try {
      const allConfigs = this.getAllConfigs();
      delete allConfigs[provider];

      if (Object.keys(allConfigs).length === 0) {
        fs.unlinkSync(this.configFile);
      } else {
        fs.writeFileSync(
          this.configFile,
          JSON.stringify(allConfigs, null, 2),
          { mode: 0o600 }
        );
      }

      console.log(`Deleted configuration for ${provider}`);
      return true;
    } catch (error) {
      console.error(`Error deleting config for ${provider}:`, error);
      throw error;
    }
  }

  clearAllConfigs() {
    try {
      if (fs.existsSync(this.configFile)) {
        fs.unlinkSync(this.configFile);
      }
      console.log('All configurations cleared');
      return true;
    } catch (error) {
      console.error('Error clearing configs:', error);
      throw error;
    }
  }
}

module.exports = { ConfigManager };
